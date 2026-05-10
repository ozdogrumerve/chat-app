# ─────────────────────────────────────────────
#  app.py  –  Main Application Controller
# ─────────────────────────────────────────────

import tkinter as tk
from tkinter import messagebox

from .gui.login_screen   import LoginScreen
from .gui.chat_screen    import ChatScreen
from .gui                import theme as T
from .network.tcp_client import TCPClient
from .network.udp_client import UDPClient
from .utils.message      import detect_message_type, format_private_cmd, is_private, parse_private


class App:
    """
    Main application controller.
    Manages the flow: Login → connect to server → open Chat screen.
    """

    def __init__(self):
        self.root = tk.Tk()
        self._online_users = []  # current user list e.g. ["Merve[TCP]", "Serhat[UDP]"]
        self._setup_window()

        self.username : str        = ""    # logged-in username
        self.protocol : str        = ""    # "TCP" or "UDP"
        self._client  : object     = None  # TCPClient or UDPClient instance
        self._chat    : ChatScreen = None  # chat screen widget, None when on login

        # Show the login screen on startup
        self._login_screen = LoginScreen(self.root, on_connect=self._on_login)

    # ── Window setup ─────────────────────────────────────────

    def _setup_window(self):
        self.root.title("TChat")
        self.root.configure(bg=T.BG_DARK)
        self.root.geometry(f"{T.WIN_W}x{T.WIN_H}")
        self.root.minsize(700, 480)
        self.root.resizable(True, True)

        # Load window icon if available
        try:
            self.root.iconbitmap("assets/icon.ico")
        except Exception:
            pass

        # Handle window close button — disconnect cleanly before exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Login ────────────────────────────────────────────────

    def _on_login(self, username: str, protocol: str,
                  host: str, tcp_port: int, udp_port: int):
        """Called by LoginScreen when the user clicks Connect."""
        self.username = username
        self.protocol = protocol

        # Create the appropriate client based on selected protocol
        if protocol == "TCP":
            self._client = TCPClient(
                host, tcp_port,
                on_message=self._on_message,
                on_disconnect=self._on_disconnected
            )
        else:
            self._client = UDPClient(
                host, udp_port,
                on_message=self._on_message,
                on_disconnect=self._on_disconnected
            )

        # Run connect() in a background thread so the UI doesn't freeze
        import threading

        def _connect():
            ok = self._client.connect()
            self.root.after(0, lambda: self._after_connect(ok))  # return to UI thread

        threading.Thread(target=_connect, daemon=True).start()

    def _after_connect(self, ok: bool):
        """Called on the UI thread after the connection attempt finishes."""
        if not ok:
            messagebox.showerror("Connection Error", "Could not connect to server.")
            return

        # Send username as the first message — server uses it for registration
        self._client.send(self.username)
        # Don't open chat screen yet — wait for the welcome message from server

    # ── Incoming messages ────────────────────────────────────

    def _on_message(self, raw: str):
        """Receive a raw message from the network thread and forward to UI thread."""
        self.root.after(0, self._process_message, raw)

    def _process_message(self, raw: str):
        """Process a raw server message on the UI thread."""

        # Chat screen not open yet — we're still in the login/registration phase
        if not self._chat:
            if "already taken" in raw:
                # Username already taken — disconnect and show error
                self._client.disconnect()
                self._client = None
                messagebox.showerror("Error", "This username is already in use!")
                return

            if "Welcome" in raw and "connected via" in raw:
                # Welcome message received — registration successful, open chat screen
                self._login_screen.place_forget()
                self._chat = ChatScreen(
                    self.root,
                    username=self.username,
                    protocol=self.protocol,
                    on_send=self._on_send,
                    on_disconnect=self._on_user_disconnect
                )
                # Show the welcome message in the chat area
                parsed = detect_message_type(raw)
                self._chat.append_message(parsed)
            return

        # Filter out server prompts that shouldn't appear in chat
        if "Enter your username" in raw:
            return

        parsed = detect_message_type(raw)

        if parsed["type"] == "userlist":
            # Update both the local cache and the sidebar
            self._online_users = parsed["users"]
            self._chat.update_users(parsed["users"])
            return

        self._chat.append_message(parsed)

    # ── Sending messages ─────────────────────────────────────

    def _on_send(self, text: str):
        """Called by ChatScreen when the user sends a message."""
        if not self._client or not self._client.is_connected:
            return

        now = __import__("datetime").datetime.now().strftime("%H:%M")

        if is_private(text):
            target, body = parse_private(text)

            # Match target against online users (case-insensitive)
            # to get the correctly cased username
            real_target = None
            for user_str in self._online_users:
                name = user_str.split("[")[0]
                if name.lower() == target.lower():
                    real_target = name
                    break

            # Target user not found in online list
            if real_target is None:
                self._chat.append_message({
                    "type": "system",
                    "body": f"User not found: {target}",
                    "ts"  : __import__("datetime").datetime.now().strftime("%H:%M"),
                })
                return

            # Prevent sending a PM to yourself
            if real_target.lower() == self.username.lower():
                self._chat.append_message({
                    "type": "system",
                    "body": "You cannot send a private message to yourself.",
                    "ts"  : __import__("datetime").datetime.now().strftime("%H:%M"),
                })
                return

            # Send PM command to server and show it locally
            self._client.send(format_private_cmd(real_target, body))
            self._chat.append_message({
                "type"    : "pm",
                "sender"  : self.username,
                "target"  : real_target,
                "protocol": self.protocol,
                "body"    : body,
                "ts"      : now,
            })

        else:
            # Public message — send to server and show locally
            self._client.send(text)
            self._chat.append_message({
                "type"    : "chat",
                "sender"  : self.username,
                "protocol": self.protocol,
                "body"    : text,
                "ts"      : now,
            })

    # ── Disconnection ────────────────────────────────────────

    def _on_user_disconnect(self):
        """Called when the user clicks the DISCONNECT button."""
        if self._client:
            # TCP: server detects disconnect automatically when socket closes
            # UDP: disconnect() closes the socket; server removes via timeout
            self._client.disconnect()
        self._return_to_login()

    def _on_disconnected(self):
        """Called by the network thread when connection is lost unexpectedly."""
        self.root.after(0, self._handle_disconnect)  # forward to UI thread

    def _handle_disconnect(self):
        """Show disconnection message and disable input."""
        if self._chat:
            self._chat.set_disconnected_mode()
            self._chat.append_message({
                "type": "system",
                "body": "Connection lost. Press DISCONNECT to return to login.",
                "ts"  : __import__("datetime").datetime.now().strftime("%H:%M"),
            })

    def _return_to_login(self):
        """Destroy the chat screen and show the login screen again."""
        if self._chat:
            self._chat.place_forget()
            self._chat.destroy()
            self._chat = None
        self._client = None
        # Re-create login screen so all fields are reset
        self._login_screen = LoginScreen(self.root, on_connect=self._on_login)

    # ── Close ────────────────────────────────────────────────

    def _on_close(self):
        """Handle window close — disconnect before destroying the window."""
        if self._client:
            self._client.disconnect()
        self.root.destroy()

    # ── Run ──────────────────────────────────────────────────

    def run(self):
        """Start the Tkinter event loop."""
        self.root.mainloop()
        