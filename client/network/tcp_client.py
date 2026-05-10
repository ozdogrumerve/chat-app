# ─────────────────────────────────────────────
#  network/tcp_client.py  –  TCP Connection Manager
# ─────────────────────────────────────────────

import socket
import threading


class TCPClient:
    def __init__(self, host: str, port: int, on_message, on_disconnect):
        """
        host          : server IP address
        port          : TCP port number
        on_message    : callable(str) — called with each incoming message line
        on_disconnect : callable()    — called when connection is lost
        """
        self.host          = host
        self.port          = port
        self.on_message    = on_message      # callback: pass received message to app
        self.on_disconnect = on_disconnect   # callback: notify app of disconnection
        self.socket        = None            # TCP socket, assigned on connect
        self._connected    = False           # connection state flag
        self._lock         = threading.Lock()  # prevents race conditions on _connected

    # ── Connection ───────────────────────────

    def connect(self) -> bool:
        """Create a TCP socket and connect to the server. Returns True on success."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # fail fast if server is unreachable
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)  # switch to blocking mode after connect
            self._connected = True

            # Start a background thread to listen for incoming messages
            t = threading.Thread(target=self._receive_loop, daemon=True)
            t.start()
            return True
        except Exception as e:
            print(f"[TCP] Connection error: {e}")
            return False

    def disconnect(self):
        """Gracefully shut down the connection."""
        with self._lock:
            if not self._connected:
                return  # already disconnected, nothing to do
            self._connected = False
        try:
            # SHUT_RDWR stops both sending and receiving before closing
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception:
            pass

    # ── Send ─────────────────────────────────

    def send(self, message: str) -> bool:
        """Encode message as UTF-8 and send to server. Returns True on success."""
        if not self._connected:
            return False
        try:
            self.socket.send(message.encode("utf-8"))
            return True
        except Exception as e:
            print(f"[TCP] Send error: {e}")
            self._handle_disconnect()  # treat send failure as a disconnection
            return False

    # ── Internal ─────────────────────────────

    def _receive_loop(self):
        """Continuously listen for incoming data from the server."""
        while self._connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    # Empty data means the server closed the connection
                    break
                # A single packet may contain multiple messages separated by newlines
                for line in data.decode("utf-8").split("\n"):
                    line = line.strip()
                    if line:
                        self.on_message(line)  # forward each line to the app
            except Exception:
                break  # any socket error also ends the loop
        self._handle_disconnect()

    def _handle_disconnect(self):
        """Clean up socket and notify the app — called only once."""
        with self._lock:
            if not self._connected:
                return  # already handled, avoid firing callback twice
            self._connected = False
        try:
            self.socket.close()
        except Exception:
            pass
        self.on_disconnect()  # notify app layer

    @property
    def is_connected(self) -> bool:
        """Read-only property to check connection state."""
        return self._connected
    