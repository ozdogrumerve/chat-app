# ─────────────────────────────────────────────
#  network/udp_client.py  –  UDP Connection Manager
# ─────────────────────────────────────────────

import socket
import threading


class UDPClient:
    def __init__(self, host: str, port: int, on_message, on_disconnect):
        """
        host          : server IP address
        port          : UDP port number
        on_message    : callable(str) — called with each incoming message line
        on_disconnect : callable()    — called when connection is lost
        """
        self.host          = host
        self.port          = port
        self.on_message    = on_message      # callback: pass received message to app
        self.on_disconnect = on_disconnect   # callback: notify app of disconnection
        self.socket        = None            # UDP socket, assigned on connect
        self._connected    = False           # connection state flag
        self._lock         = threading.Lock()  # prevents race conditions on _connected

    # ── Connection ───────────────────────────

    def connect(self) -> bool:
        """Create a UDP socket and start the receive loop. Returns True on success."""
        try:
            # SOCK_DGRAM = UDP (connectionless, no handshake)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # UDP has no connection state, so recv would block forever without a timeout
            self.socket.settimeout(1.0)
            self._connected = True

            # Start background thread to listen for incoming messages
            t = threading.Thread(target=self._receive_loop, daemon=True)
            t.start()
            return True
        except Exception as e:
            print(f"[UDP] Socket error: {e}")
            return False

    def disconnect(self):
        """Close the socket and mark as disconnected."""
        with self._lock:
            if not self._connected:
                return  # already disconnected, nothing to do
            self._connected = False
        try:
            self.socket.close()
        except Exception:
            pass

    # ── Send ─────────────────────────────────

    def send(self, message: str) -> bool:
        """Encode message as UTF-8 and send as a UDP datagram to the server."""
        if not self._connected:
            return False
        try:
            # sendto is used instead of send because UDP has no persistent connection
            self.socket.sendto(message.encode("utf-8"), (self.host, self.port))
            return True
        except Exception as e:
            print(f"[UDP] Send error: {e}")
            return False

    # ── Internal ─────────────────────────────

    def _receive_loop(self):
        """Continuously listen for incoming UDP datagrams from the server."""
        while self._connected:
            try:
                data, _ = self.socket.recvfrom(4096)  # _ discards the sender address
                # A single datagram may contain multiple newline-separated messages
                for line in data.decode("utf-8").split("\n"):
                    line = line.strip()
                    if line:
                        self.on_message(line)  # forward each line to the app
            except socket.timeout:
                # Timeout is expected — UDP has no keep-alive, loop and try again
                continue
            except Exception:
                break  # any other socket error ends the loop
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
    