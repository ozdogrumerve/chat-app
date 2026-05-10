# ─────────────────────────────────────────────
#  server/server.py  –  TCP + UDP Hybrid Server
#  Features: broadcast, private messaging, user list
# ─────────────────────────────────────────────

import socket
import threading
import time

HOST        = "127.0.0.1"
TCP_PORT    = 12345
UDP_PORT    = 12346
BUFFER_SIZE = 4096

tcp_clients  = {}   # socket  → {username, address, protocol}
udp_clients  = {}   # address → {username, address, protocol}
clients_lock = threading.Lock()  # shared lock for both client dicts


# ── UDP Heartbeat ─────────────────────────────────────────────

# Tracks the last time a message was received from each UDP client
udp_last_seen = {}  # address → timestamp (float)

def udp_heartbeat_checker():
    """Every 30 seconds, remove UDP clients that have been silent for over 60 seconds."""
    while True:
        time.sleep(30)
        now = time.time()
        stale = []

        # Collect addresses of clients that have timed out
        with clients_lock:
            for addr in list(udp_clients.keys()):
                last = udp_last_seen.get(addr, 0)
                if now - last > 60:
                    stale.append(addr)

        # Remove stale clients outside the lock to avoid deadlocks
        for addr in stale:
            print(f"[UDP] Timeout: {addr}")
            remove_udp_client(addr)


# ── Helpers ───────────────────────────────────────────────────

def username_exists(username: str) -> bool:
    """Check if a username is already taken (case-insensitive)."""
    ulow = username.lower()
    for info in tcp_clients.values():
        if info["username"].lower() == ulow:
            return True
    for info in udp_clients.values():
        if info["username"].lower() == ulow:
            return True
    return False


def get_user_list() -> list:
    """Return all online users in 'Name[PROTO]' format."""
    result = []
    for info in tcp_clients.values():
        result.append(f"{info['username']}[TCP]")
    for info in udp_clients.values():
        result.append(f"{info['username']}[UDP]")
    return result


def broadcast_userlist():
    """Send the current user list to all connected clients."""
    with clients_lock:
        users = get_user_list()
    msg = "/userlist " + ",".join(users)
    broadcast(msg)


def broadcast(message: str, sender_type=None,
              sender_socket=None, sender_address=None):
    """Send a message to all clients except the original sender."""
    with clients_lock:
        tcp_list = list(tcp_clients.items())
        udp_list = list(udp_clients.items())

    # Send to all TCP clients except the sender
    for sock, info in tcp_list:
        if sender_type == "TCP" and sock == sender_socket:
            continue
        try:
            sock.send((message + "\n").encode("utf-8"))
        except Exception:
            remove_tcp_client(sock)

    # Send to all UDP clients except the sender
    for addr, info in udp_list:
        if sender_type == "UDP" and addr == sender_address:
            continue
        try:
            udp_server_socket.sendto((message + "\n").encode("utf-8"), addr)
        except Exception:
            pass


def send_to_username(target_username: str, message: str) -> bool:
    """Send a message to a specific user by username. Returns True on success."""
    with clients_lock:
        # Search TCP clients first
        for sock, info in tcp_clients.items():
            if info["username"].lower() == target_username.lower():
                try:
                    sock.send((message + "\n").encode("utf-8"))
                    return True
                except Exception:
                    return False
        # Then search UDP clients
        for addr, info in udp_clients.items():
            if info["username"].lower() == target_username.lower():
                try:
                    udp_server_socket.sendto((message + "\n").encode("utf-8"), addr)
                    return True
                except Exception:
                    return False
    return False  # user not found


# ── TCP ──────────────────────────────────────────────────────

def remove_tcp_client(client_socket):
    """Remove a TCP client, close their socket, and notify others."""
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
    """Handle the full lifecycle of a TCP client connection."""
    try:
        # ── Username registration loop ────────────────────────
        while True:
            client_socket.send("Kullanici adinizi giriniz: \n".encode("utf-8"))
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                return  # client disconnected before registering
            username = data.decode("utf-8").strip()
            if not username:
                continue

            with clients_lock:
                used = username_exists(username)
                if not used:
                    # Register the client
                    tcp_clients[client_socket] = {
                        "username" : username,
                        "address"  : client_address,
                        "protocol" : "TCP"
                    }

            if used:
                # Notify client that the username is taken and ask again
                warning = (
                    "Bu kullanici zaten sohbet odasinda, "
                    "lutfen baska bir kullanici adi giriniz!\n"
                )
                client_socket.send(warning.encode("utf-8"))
            else:
                break  # username accepted

        # ── Welcome and join notification ─────────────────────
        client_socket.send(
            f"Hosgeldiniz {username}, [TCP] ile baglisiniz!\n".encode("utf-8")
        )
        join_msg = f"{username} - [TCP] ile sohbet odasina katildi."
        print(join_msg)
        broadcast(join_msg, sender_type="TCP", sender_socket=client_socket)
        broadcast_userlist()

        # ── Message loop ──────────────────────────────────────
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break  # client disconnected
            message = data.decode("utf-8").strip()
            if not message:
                continue

            # Handle private message command
            if message.startswith("/pm "):
                _handle_pm(message, username, "TCP", client_socket, None)
                continue

            # Broadcast public message to everyone else
            formatted = f"{username}[TCP] : {message}"
            print(formatted)
            broadcast(formatted, sender_type="TCP", sender_socket=client_socket)

    except Exception:
        pass
    finally:
        # Always clean up, even on unexpected errors
        remove_tcp_client(client_socket)


def _handle_pm(raw_cmd: str, sender: str, proto: str,
               sender_socket=None, sender_address=None):
    """Parse and deliver a private message: /pm target body"""
    parts = raw_cmd.split(" ", 2)
    if len(parts) < 3:
        return  # malformed command, ignore

    target  = parts[1]
    body    = parts[2]

    # Format received by the target: "[PM|sender] Sender[TCP] : body"
    pm_msg = f"[PM|{sender}] {sender}[{proto}] : {body}"
    ok = send_to_username(target, pm_msg)

    # If target not found, notify the sender
    if not ok:
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
    """Continuously accept incoming TCP connections and spawn a thread for each."""
    while True:
        try:
            sock, addr = tcp_server_socket.accept()
            t = threading.Thread(target=handle_tcp_client, args=(sock, addr), daemon=True)
            t.start()
        except Exception:
            continue


# ── UDP ──────────────────────────────────────────────────────

def remove_udp_client(client_address):
    """Remove a UDP client and notify others."""
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
    """Handle a single incoming UDP datagram."""
    text = message.decode("utf-8").strip()
    if not text:
        return

    with clients_lock:
        is_registered = client_address in udp_clients

    if not is_registered:
        # ── First message = username registration ─────────────
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
            # Username taken — notify and wait for another attempt
            warning = (
                "Bu kullanici zaten sohbet odasinda, "
                "lutfen baska bir kullanici adi giriniz!\n"
            )
            udp_server_socket.sendto(warning.encode("utf-8"), client_address)
            return

        # Registration successful — welcome and notify others
        udp_server_socket.sendto(
            f"Hosgeldiniz {username}, [UDP] ile baglisiniz!\n".encode("utf-8"),
            client_address
        )
        join_msg = f"{username} - [UDP] ile sohbet odasina katildi."
        print(join_msg)
        broadcast(join_msg, sender_type="UDP", sender_address=client_address)
        broadcast_userlist()
        udp_last_seen[client_address] = time.time()  # record first seen time
        return

    # ── Registered client — handle their message ──────────────
    with clients_lock:
        username = udp_clients[client_address]["username"]

    # Update last seen time on every message
    udp_last_seen[client_address] = time.time()

    # Handle private message command
    if text.startswith("/pm "):
        _handle_pm(text, username, "UDP", None, client_address)
        return

    # Broadcast public message to everyone else
    formatted = f"{username}[UDP] : {text}"
    print(formatted)
    broadcast(formatted, sender_type="UDP", sender_address=client_address)


def listen_udp_clients():
    """Continuously receive UDP datagrams and handle each in a new thread."""
    while True:
        try:
            data, addr = udp_server_socket.recvfrom(BUFFER_SIZE)
            t = threading.Thread(target=handle_udp_message, args=(data, addr), daemon=True)
            t.start()
        except ConnectionResetError:
            continue  # common on Windows when a UDP client disappears
        except Exception:
            continue


# ── Startup ───────────────────────────────────────────────────

# Create and bind TCP server socket
tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow port reuse after restart
tcp_server_socket.bind((HOST, TCP_PORT))
tcp_server_socket.listen()

# Create and bind UDP server socket
udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server_socket.bind((HOST, UDP_PORT))

print("=" * 40)
print("  TChat Server Started")
print("=" * 40)
print(f"  TCP  →  {HOST}:{TCP_PORT}")
print(f"  UDP  →  {HOST}:{UDP_PORT}")
print("=" * 40)

# Start TCP accept loop
tcp_thread = threading.Thread(target=accept_tcp_clients, daemon=True)
tcp_thread.start()

# Start UDP receive loop
udp_thread = threading.Thread(target=listen_udp_clients, daemon=True)
udp_thread.start()

# Start UDP heartbeat checker
hb_thread = threading.Thread(target=udp_heartbeat_checker, daemon=True)
hb_thread.start()

# Keep the main thread alive
while True:
    threading.Event().wait(1)
    