# ─────────────────────────────────────────────
#  gui/chat_screen.py  –  Main Chat Screen
# ─────────────────────────────────────────────

import tkinter as tk
from tkinter import scrolledtext
from .user_list import UserListPanel
from . import theme as T


class ChatScreen(tk.Frame):
    """
    Main chat interface:
    - Left  : online user list (sidebar)
    - Center: message area (color-coded)
    - Bottom: input field + send button + disconnect
    """

    def __init__(self, master, username: str, protocol: str,
                 on_send, on_disconnect):
        super().__init__(master, bg=T.BG_DARK)
        self.username      = username    # logged-in username
        self.protocol      = protocol    # "TCP" or "UDP"
        self.on_send       = on_send     # callback: send message to server
        self.on_disconnect = on_disconnect  # callback: disconnect button
        self._build()

    def _build(self):
        # Fill the entire parent window
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Top bar ──────────────────────────────────────────
        topbar = tk.Frame(self, bg=T.BG_PANEL, height=48)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        # App title label
        tk.Label(
            topbar, text="◈  TCHAT", font=("Consolas", 13, "bold"),
            fg=T.ACCENT, bg=T.BG_PANEL
        ).pack(side="left", padx=18, pady=10)

        # Protocol badge — blue for TCP, orange for UDP
        proto_color = T.ACCENT_TCP if self.protocol == "TCP" else T.ACCENT_UDP
        tk.Label(
            topbar,
            text=f" {self.protocol} ",
            font=("Consolas", 9, "bold"),
            fg=T.BG_DARK, bg=proto_color,
        ).pack(side="left", pady=14)

        # Logged-in username display
        tk.Label(
            topbar, text=f"@{self.username}",
            font=T.FONT_UI_S, fg=T.TEXT_SECONDARY, bg=T.BG_PANEL
        ).pack(side="left", padx=10)

        # Connection status indicator (right side)
        self._status_lbl = tk.Label(
            topbar, text="● Bağlı",
            font=T.FONT_UI_S, fg=T.SUCCESS, bg=T.BG_PANEL
        )
        self._status_lbl.pack(side="right", padx=18)

        # Disconnect button — triggers on_disconnect callback
        disc_btn = tk.Button(
            topbar, text="AYRIL",
            font=("Consolas", 9, "bold"),
            fg=T.DANGER, bg=T.BG_PANEL,
            activeforeground=T.BG_DARK, activebackground=T.DANGER,
            relief="flat", cursor="hand2", bd=0,
            padx=12, pady=0,
            command=self.on_disconnect
        )
        disc_btn.pack(side="right")

        # Horizontal divider below top bar
        tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x", side="top")

        # ── Main content: sidebar + message area ─────────────
        content = tk.Frame(self, bg=T.BG_DARK)
        content.pack(fill="both", expand=True, side="top")

        # Left sidebar: online user list
        self._user_panel = UserListPanel(content, on_pm_click=self._insert_pm)
        self._user_panel.pack(side="left", fill="y")

        # Vertical divider between sidebar and message area
        tk.Frame(content, bg=T.BORDER, width=1).pack(side="left", fill="y")

        # Container for message area + scrollbar
        msg_container = tk.Frame(content, bg=T.BG_DARK)
        msg_container.pack(side="left", fill="both", expand=True)

        # Read-only text widget for displaying chat messages
        self._msg_area = tk.Text(
            msg_container,
            bg=T.BG_DARK,
            fg=T.TEXT_PRIMARY,
            font=T.FONT_MONO,
            relief="flat",
            bd=0,
            padx=16,
            pady=12,
            wrap="word",
            state="disabled",  # users cannot type here directly
            cursor="arrow",
        )
        self._msg_area.pack(fill="both", expand=True, padx=0, pady=0)

        # Vertical scrollbar for the message area
        scrollbar = tk.Scrollbar(
            msg_container, orient="vertical",
            command=self._msg_area.yview,
            bg=T.SCROLLBAR_BG, troughcolor=T.SCROLLBAR_BG,
            activebackground=T.SCROLLBAR_FG
        )
        self._msg_area.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Apply color tags for different message types
        self._configure_tags()

        # ── Bottom input bar ──────────────────────────────────
        tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x", side="top")

        input_bar = tk.Frame(self, bg=T.BG_PANEL, height=T.INPUT_H)
        input_bar.pack(fill="x", side="bottom")
        input_bar.pack_propagate(False)

        # Text input field — Enter key triggers send
        self._input = tk.Entry(
            input_bar,
            font=("Consolas", 11),
            fg=T.TEXT_PRIMARY,
            bg=T.BG_CARD,
            insertbackground=T.ACCENT,
            relief="flat",
            bd=0,
        )
        self._input.pack(side="left", fill="both", expand=True, padx=12, pady=8, ipady=4)
        self._input.bind("<Return>", lambda _: self._send())
        self._input.focus_set()

        # PM hint label — shows "@user →" when typing a private message
        self._pm_hint = tk.Label(
            input_bar, text="",
            font=T.FONT_SMALL, fg=T.ACCENT_PM, bg=T.BG_PANEL
        )
        self._pm_hint.pack(side="left", padx=(0, 6))
        self._input.bind("<KeyRelease>", self._update_pm_hint)

        # Send button
        send_btn = tk.Button(
            input_bar, text="SEND",
            font=("Consolas", 10, "bold"),
            fg=T.BG_DARK, bg=T.ACCENT,
            activeforeground=T.BG_DARK, activebackground=T.ACCENT_DIM,
            relief="flat", cursor="hand2", bd=0,
            padx=18,
            command=self._send
        )
        send_btn.pack(side="right", padx=(0, 12), pady=8)

    # ── Color tags ───────────────────────────────────────────

    def _configure_tags(self):
        """Define named color/font tags used when inserting text."""
        a = self._msg_area
        a.tag_config("ts",       foreground=T.TEXT_MUTED,    font=("Consolas", 9))           # timestamp
        a.tag_config("sender",   foreground=T.ACCENT,        font=("Consolas", 11, "bold"))  # other user's name
        a.tag_config("self",     foreground=T.SUCCESS,       font=("Consolas", 11, "bold"))  # own name
        a.tag_config("tcp",      foreground=T.ACCENT_TCP,    font=("Consolas", 9, "bold"))   # [TCP] badge
        a.tag_config("udp",      foreground=T.ACCENT_UDP,    font=("Consolas", 9, "bold"))   # [UDP] badge
        a.tag_config("body",     foreground=T.TEXT_PRIMARY,  font=T.FONT_MONO)               # message body
        a.tag_config("system",   foreground=T.TEXT_SECONDARY,font=("Consolas", 10, "italic"))# system info
        a.tag_config("join",     foreground=T.SUCCESS,       font=("Consolas", 10, "italic"))# user joined
        a.tag_config("leave",    foreground=T.DANGER,        font=("Consolas", 10, "italic"))# user left
        a.tag_config("pm_in",    foreground=T.ACCENT_PM,     font=("Consolas", 11, "bold"))  # PM label
        a.tag_config("pm_body",  foreground=T.ACCENT_PM,     font=T.FONT_MONO)               # PM body
        a.tag_config("divider",  foreground=T.TEXT_MUTED,    font=("Consolas", 8))           # divider line

    # ── Message rendering ─────────────────────────────────────

    def append_message(self, parsed: dict):
        """Render a parsed message dict into the message area."""
        self._msg_area.config(state="normal")

        mtype = parsed.get("type", "system")

        if mtype == "chat":
            self._append_chat(parsed)
        elif mtype == "pm":
            self._append_pm(parsed)
        elif mtype in ("join", "leave"):
            self._append_event(parsed)
        elif mtype == "userlist":
            pass  # userlist only updates the sidebar, not the message area
        else:
            self._append_system(parsed)

        self._msg_area.config(state="disabled")
        self._msg_area.see("end")  # auto-scroll to latest message

    def _append_chat(self, p):
        """Render a public chat message."""
        is_self = (p["sender"] == self.username)  # highlight own messages
        proto   = p.get("protocol", "")
        ts_text  = f" {p['ts']} "
        sender   = p["sender"]
        body     = p["body"]

        self._insert("ts",     ts_text)
        self._insert("self" if is_self else "sender", sender)
        self._insert("tcp" if proto == "TCP" else "udp", f"[{proto}] ")
        self._insert("body",   body + "\n")

    def _append_pm(self, p):
        """Render a private message (incoming or outgoing)."""
        is_outgoing = (p.get("sender", "") == self.username)
        label = f"[PM → {p.get('target','')}]" if is_outgoing else f"[PM ← {p['sender']}]"

        self._insert("ts",      f" {p['ts']} ")
        self._insert("pm_in",   label + " ")
        self._insert("pm_body", p["body"] + "\n")

    def _append_event(self, p):
        """Render a join or leave event."""
        symbol = "+" if p["type"] == "join" else "−"
        tag    = "join" if p["type"] == "join" else "leave"
        self._insert(tag, f" {p['ts']}  {symbol} {p['body']}\n")

    def _append_system(self, p):
        """Render a system/info message (welcome, errors, etc.)."""
        self._insert("system", f" {p['ts']}  ⓘ {p['body']}\n")

    def _insert(self, tag: str, text: str):
        """Insert styled text into the message area."""
        self._msg_area.insert("end", text, tag)

    # ── Send ─────────────────────────────────────────────────

    def _send(self):
        """Read input, clear field, and pass text to on_send callback."""
        text = self._input.get().strip()
        if not text:
            return
        self._input.delete(0, "end")
        self._pm_hint.config(text="")
        self.on_send(text)

    # ── PM hint ──────────────────────────────────────────────

    def _update_pm_hint(self, event=None):
        """Show a live hint when the user is typing a private message."""
        text = self._input.get()
        if text.startswith("@") and " " not in text:
            self._pm_hint.config(text="PM: @user message")
        elif text.startswith("@") and " " in text:
            target = text.split(" ", 1)[0][1:]
            self._pm_hint.config(text=f"→ @{target}")
        else:
            self._pm_hint.config(text="")

    def _insert_pm(self, username: str):
        """Auto-fill input with @username when clicking a user in the sidebar."""
        current = self._input.get()
        if not current.startswith("@"):
            self._input.delete(0, "end")
            self._input.insert(0, f"@{username} ")
        self._input.focus_set()

    # ── Public methods ───────────────────────────────────────

    def update_users(self, users: list):
        """Forward updated user list to the sidebar panel."""
        self._user_panel.update_users(users, own_username=self.username)

    def set_status(self, connected: bool):
        """Update the connection status label in the top bar."""
        if connected:
            self._status_lbl.config(text="● Connected", fg=T.SUCCESS)
        else:
            self._status_lbl.config(text="● Disconnected", fg=T.DANGER)

    def set_disconnected_mode(self):
        """Disable input field after connection is lost."""
        self._input.config(state="disabled")
        self.set_status(False)