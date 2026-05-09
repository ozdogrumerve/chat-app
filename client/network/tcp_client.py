# ─────────────────────────────────────────────
#  network/tcp_client.py  –  TCP Bağlantı Yöneticisi
# ─────────────────────────────────────────────

import socket
import threading


class TCPClient:
    def __init__(self, host: str, port: int, on_message, on_disconnect):
        """
        host          : server IP
        port          : TCP port
        on_message    : callable(str) – gelen mesajı iletir
        on_disconnect : callable()    – bağlantı kopunca çağrılır
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
        """Server'a bağlan. Başarılıysa True döner."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)
            self._connected = True

            # Dinleme thread'ini başlat
            t = threading.Thread(target=self._receive_loop, daemon=True)
            t.start()
            return True
        except Exception as e:
            print(f"[TCP] Bağlantı hatası: {e}")
            return False

    def disconnect(self):
        """Bağlantıyı düzgün şekilde kapat."""
        with self._lock:
            if not self._connected:
                return
            self._connected = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception:
            pass

    # ── Mesaj Gönder ─────────────────────────

    def send(self, message: str) -> bool:
        """Mesajı UTF-8 ile encode edip gönder."""
        if not self._connected:
            return False
        try:
            self.socket.send(message.encode("utf-8"))
            return True
        except Exception as e:
            print(f"[TCP] Gönderim hatası: {e}")
            self._handle_disconnect()
            return False

    # ── Dahili ───────────────────────────────

    def _receive_loop(self):
        """Serverdan gelen mesajları sürekli dinler."""
        while self._connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                # Tek pakette birden fazla mesaj gelebilir; satır satır ayır
                for line in data.decode("utf-8").split("\n"):
                    line = line.strip()
                    if line:
                        self.on_message(line)
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
