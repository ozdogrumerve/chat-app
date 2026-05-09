# ─────────────────────────────────────────────
#  server/server.py  –  TCP + UDP Hybrid Server
#  Özellikler: broadcast, private msg, userlist
# ─────────────────────────────────────────────

import socket
import threading

HOST        = "127.0.0.1"
TCP_PORT    = 12345
UDP_PORT    = 12346
BUFFER_SIZE = 4096

tcp_clients  = {}   # socket → {username, address, protocol}
udp_clients  = {}   # address → {username, address, protocol}
clients_lock = threading.Lock()


# ── Yardımcı ─────────────────────────────────────────────────

def username_exists(username: str) -> bool:
    ulow = username.lower()
    for info in tcp_clients.values():
        if info["username"].lower() == ulow:
            return True
    for info in udp_clients.values():
        if info["username"].lower() == ulow:
            return True
    return False


def get_user_list() -> list:
    """Tüm online kullanıcıları 'Ad[PROTO]' formatında döndürür."""
    result = []
    for info in tcp_clients.values():
        result.append(f"{info['username']}[TCP]")
    for info in udp_clients.values():
        result.append(f"{info['username']}[UDP]")
    return result


def broadcast_userlist():
    """Tüm clientlara güncel kullanıcı listesini gönderir."""
    with clients_lock:
        users = get_user_list()
    msg = "/userlist " + ",".join(users)
    broadcast(msg)


def broadcast(message: str, sender_type=None,
              sender_socket=None, sender_address=None):
    """Mesajı gönderen hariç herkese yollar."""
    with clients_lock:
        tcp_list = list(tcp_clients.items())
        udp_list = list(udp_clients.items())

    for sock, info in tcp_list:
        if sender_type == "TCP" and sock == sender_socket:
            continue
        try:
            sock.send((message + "\n").encode("utf-8"))
        except Exception:
            remove_tcp_client(sock)

    for addr, info in udp_list:
        if sender_type == "UDP" and addr == sender_address:
            continue
        try:
            udp_server_socket.sendto((message + "\n").encode("utf-8"), addr)
        except Exception:
            pass


def send_to_username(target_username: str, message: str) -> bool:
    """Belirli bir kullanıcıya mesaj gönderir. Başarılıysa True."""
    with clients_lock:
        for sock, info in tcp_clients.items():
            if info["username"].lower() == target_username.lower():
                try:
                    sock.send((message + "\n").encode("utf-8"))
                    return True
                except Exception:
                    return False
        for addr, info in udp_clients.items():
            if info["username"].lower() == target_username.lower():
                try:
                    udp_server_socket.sendto((message + "\n").encode("utf-8"), addr)
                    return True
                except Exception:
                    return False
    return False


# ── TCP ──────────────────────────────────────────────────────

def remove_tcp_client(client_socket):
    with clients_lock:
        if client_socket not in tcp_clients:
            return
        username = tcp_clients[client_socket]["username"]
        del tcp_clients[client_socket]
    try:
        client_socket.close()
    except Exception:
        pass
    msg = f"{username} - [TCP] sohbet odasindan ayrildi"
    print(msg)
    broadcast(msg)
    broadcast_userlist()


def handle_tcp_client(client_socket, client_address):
    try:
        # Kullanıcı adı alma döngüsü
        while True:
            client_socket.send("Kullanici adinizi giriniz: \n".encode("utf-8"))
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                return
            username = data.decode("utf-8").strip()
            if not username:
                continue

            with clients_lock:
                used = username_exists(username)
                if not used:
                    tcp_clients[client_socket] = {
                        "username" : username,
                        "address"  : client_address,
                        "protocol" : "TCP"
                    }

            if used:
                warning = (
                    "Bu kullanici zaten sohbet odasinda, "
                    "lutfen baska bir kullanici adi giriniz!\n"
                )
                client_socket.send(warning.encode("utf-8"))
            else:
                break

        # Hoş geldin
        client_socket.send(
            f"Hosgeldiniz {username}, [TCP] ile baglisiniz!\n".encode("utf-8")
        )

        join_msg = f"{username} - [TCP] ile sohbet odasina katildi."
        print(join_msg)
        broadcast(join_msg, sender_type="TCP", sender_socket=client_socket)
        broadcast_userlist()

        # Mesaj dinleme
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            message = data.decode("utf-8").strip()
            if not message:
                continue

            # Private mesaj komutu: /pm hedef mesaj
            if message.startswith("/pm "):
                _handle_pm(message, username, "TCP", client_socket, None)
                continue

            formatted = f"{username}[TCP] : {message}"
            print(formatted)
            broadcast(formatted, sender_type="TCP", sender_socket=client_socket)

    except Exception:
        pass
    finally:
        remove_tcp_client(client_socket)


def _handle_pm(raw_cmd: str, sender: str, proto: str,
               sender_socket=None, sender_address=None):
    """Private mesaj işle: /pm hedef mesaj"""
    parts = raw_cmd.split(" ", 2)
    if len(parts) < 3:
        return
    target  = parts[1]
    body    = parts[2]
    pm_msg  = f"[PM|{sender}] {sender}[{proto}] : {body}"
    ok = send_to_username(target, pm_msg)

    if not ok:
        # Sadece hata durumunda bildir
        err = f"[PM] Kullanıcı bulunamadı: {target}"
        if sender_socket:
            try:
                sender_socket.send((err + "\n").encode("utf-8"))
            except Exception:
                pass
        elif sender_address:
            try:
                udp_server_socket.sendto((err + "\n").encode("utf-8"), sender_address)
            except Exception:
                pass


def accept_tcp_clients():
    while True:
        try:
            sock, addr = tcp_server_socket.accept()
            t = threading.Thread(target=handle_tcp_client, args=(sock, addr), daemon=True)
            t.start()
        except Exception:
            continue


# ── UDP ──────────────────────────────────────────────────────

def remove_udp_client(client_address):
    with clients_lock:
        if client_address not in udp_clients:
            return
        username = udp_clients[client_address]["username"]
        del udp_clients[client_address]
    msg = f"{username} - [UDP] sohbet odasindan ayrildi"
    print(msg)
    broadcast(msg, sender_type="UDP", sender_address=client_address)
    broadcast_userlist()


def handle_udp_message(message: bytes, client_address):
    text = message.decode("utf-8").strip()
    if not text:
        return

    with clients_lock:
        is_registered = client_address in udp_clients

    if not is_registered:
        # İlk mesaj = kullanıcı adı
        username = text
        with clients_lock:
            used = username_exists(username)
            if not used:
                udp_clients[client_address] = {
                    "username" : username,
                    "address"  : client_address,
                    "protocol" : "UDP"
                }

        if used:
            warning = (
                "Bu kullanici zaten sohbet odasinda, "
                "lutfen baska bir kullanici adi giriniz!\n"
            )
            udp_server_socket.sendto(warning.encode("utf-8"), client_address)
            return

        udp_server_socket.sendto(
            f"Hosgeldiniz {username}, [UDP] ile baglisiniz!\n".encode("utf-8"),
            client_address
        )
        join_msg = f"{username} - [UDP] ile sohbet odasina katildi."
        print(join_msg)
        broadcast(join_msg, sender_type="UDP", sender_address=client_address)
        broadcast_userlist()
        return

    with clients_lock:
        username = udp_clients[client_address]["username"]

    if text == "Gorusuruz":
        remove_udp_client(client_address)
        return

    # Private mesaj
    if text.startswith("/pm "):
        _handle_pm(text, username, "UDP", None, client_address)
        return

    formatted = f"{username}[UDP] : {text}"
    print(formatted)
    broadcast(formatted, sender_type="UDP", sender_address=client_address)


def listen_udp_clients():
    while True:
        try:
            data, addr = udp_server_socket.recvfrom(BUFFER_SIZE)
            t = threading.Thread(target=handle_udp_message, args=(data, addr), daemon=True)
            t.start()
        except ConnectionResetError:
            continue
        except Exception:
            continue


# ── Başlatma ─────────────────────────────────────────────────

tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_server_socket.bind((HOST, TCP_PORT))
tcp_server_socket.listen()

udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server_socket.bind((HOST, UDP_PORT))

print("=" * 40)
print("  TChat Server Başlatıldı")
print("=" * 40)
print(f"  TCP  →  {HOST}:{TCP_PORT}")
print(f"  UDP  →  {HOST}:{UDP_PORT}")
print("=" * 40)

tcp_thread = threading.Thread(target=accept_tcp_clients, daemon=True)
tcp_thread.start()

udp_thread = threading.Thread(target=listen_udp_clients, daemon=True)
udp_thread.start()

# Sürekli çalış
while True:
    threading.Event().wait(1)
