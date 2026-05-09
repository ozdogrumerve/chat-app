# ─────────────────────────────────────────────
#  network/udp_client.py  –  UDP Bağlantı Yöneticisi
# ─────────────────────────────────────────────

import socket
import threading


class UDPClient:
    def __init__(self, host: str, port: int, on_message, on_disconnect):
        """
        host          : server IP
        port          : UDP port
        on_message    : callable(str)
        on_disconnect : callable()
        """
        self.host          = host
        self.port          = port
        self.on_message    = on_message
        self.on_disconnect = on_disconnect
        self.socket        = None
        self._connected    = False
        self._lock         = threading.Lock()

    # ── Bağlantı ─────────────────────────────

    def connect(self) -> bool:
        """UDP socketi oluştur ve kullanıcı adını gönder."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # UDP bağlantısız protokol; receive timeout koyuyoruz
            self.socket.settimeout(1.0)
            self._connected = True

            # Dinleme thread'i
            t = threading.Thread(target=self._receive_loop, daemon=True)
            t.start()
            return True
        except Exception as e:
            print(f"[UDP] Socket hatası: {e}")
            return False

    def disconnect(self):
        """Ayrılma mesajı gönder ve socketi kapat."""
        with self._lock:
            if not self._connected:
                return
            self._connected = False
        try:
            # Server'a ayrılma sinyali gönder
            self.socket.sendto("Gorusuruz".encode("utf-8"), (self.host, self.port))
            self.socket.close()
        except Exception:
            pass

    # ── Mesaj Gönder ─────────────────────────

    def send(self, message: str) -> bool:
        if not self._connected:
            return False
        try:
            self.socket.sendto(message.encode("utf-8"), (self.host, self.port))
            return True
        except Exception as e:
            print(f"[UDP] Gönderim hatası: {e}")
            return False

    # ── Dahili ───────────────────────────────

    def _receive_loop(self):
        while self._connected:
            try:
                data, _ = self.socket.recvfrom(4096)
                for line in data.decode("utf-8").split("\n"):
                    line = line.strip()
                    if line:
                        self.on_message(line)
            except socket.timeout:
                # Timeout normal; döngüye devam et
                continue
            except Exception:
                break
        self._handle_disconnect()

    def _handle_disconnect(self):
        with self._lock:
            if not self._connected:
                return
            self._connected = False
        try:
            self.socket.close()
        except Exception:
            pass
        self.on_disconnect()

    @property
    def is_connected(self) -> bool:
        return self._connected
