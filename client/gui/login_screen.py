# ─────────────────────────────────────────────
#  gui/login_screen.py  –  Giriş Ekranı
# ─────────────────────────────────────────────

import tkinter as tk
from tkinter import messagebox
from . import theme as T


class LoginScreen(tk.Frame):
    """
    Protokol seçimi (TCP / UDP), kullanıcı adı,
    host ve port girişi yapılan ekran.
    on_connect(username, protocol, host, tcp_port, udp_port)
    """

    def __init__(self, master, on_connect):
        super().__init__(master, bg=T.BG_DARK)
        self.on_connect = on_connect
        self._build()

    def _build(self):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Merkez kart ──────────────────────────────────────
        card = tk.Frame(self, bg=T.BG_PANEL, padx=40, pady=36)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Başlık
        tk.Label(
            card, text="◈  TCHAT", font=("Consolas", 22, "bold"),
            fg=T.ACCENT, bg=T.BG_PANEL
        ).grid(row=0, column=0, columnspan=2, pady=(0, 4))

        tk.Label(
            card, text="TCP / UDP Chat Application",
            font=T.FONT_UI_S, fg=T.TEXT_SECONDARY, bg=T.BG_PANEL
        ).grid(row=1, column=0, columnspan=2, pady=(0, 28))

        # ── Protokol ─────────────────────────────────────────
        self._protocol = tk.StringVar(value="TCP")

        tk.Label(
            card, text="PROTOCOL", font=T.FONT_SMALL,
            fg=T.TEXT_SECONDARY, bg=T.BG_PANEL
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 6))

        proto_frame = tk.Frame(card, bg=T.BG_PANEL)
        proto_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        for text, val, color in [("TCP", "TCP", T.ACCENT_TCP), ("UDP", "UDP", T.ACCENT_UDP)]:
            btn = tk.Radiobutton(
                proto_frame, text=text, variable=self._protocol, value=val,
                font=("Consolas", 11, "bold"),
                fg=color, bg=T.BG_CARD,
                selectcolor=T.BG_HOVER,
                activebackground=T.BG_HOVER, activeforeground=color,
                relief="flat", cursor="hand2",
                padx=20, pady=8,
                indicatoron=False,
                bd=0
            )
            btn.pack(side="left", padx=(0, 8))

        # ── Host ─────────────────────────────────────────────
        self._host = self._field(card, "HOST", "127.0.0.1", row=4)

        # ── TCP Port ─────────────────────────────────────────
        self._tcp_port = self._field(card, "TCP PORT", "12345", row=6)

        # ── UDP Port ─────────────────────────────────────────
        self._udp_port = self._field(card, "UDP PORT", "12346", row=8)

        # ── Kullanıcı Adı ─────────────────────────────────────
        self._username = self._field(card, "USERNAME", "", row=10, focus=True)

        # ── Bağlan Butonu ─────────────────────────────────────
        connect_btn = tk.Button(
            card, text="CONNECT  →",
            font=("Consolas", 12, "bold"),
            fg=T.BG_DARK, bg=T.ACCENT,
            activeforeground=T.BG_DARK, activebackground=T.ACCENT_DIM,
            relief="flat", cursor="hand2",
            padx=0, pady=12,
            command=self._attempt_connect
        )
        connect_btn.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(24, 0))

        # Enter tuşu
        self._username.bind("<Return>", lambda _: self._attempt_connect())

        # Alt bilgi
        tk.Label(
            card, text="@USER message  →  private message",
            font=T.FONT_SMALL, fg=T.TEXT_MUTED, bg=T.BG_PANEL
        ).grid(row=13, column=0, columnspan=2, pady=(14, 0))

    def _field(self, parent, label: str, placeholder: str, row: int, focus=False):
        """Label + Entry çifti oluşturur, Entry'yi döndürür."""
        tk.Label(
            parent, text=label, font=T.FONT_SMALL,
            fg=T.TEXT_SECONDARY, bg=T.BG_PANEL
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))

        entry = tk.Entry(
            parent,
            font=("Consolas", 11),
            fg=T.TEXT_PRIMARY,
            bg=T.BG_CARD,
            insertbackground=T.ACCENT,
            relief="flat",
            bd=0,
            width=30,
        )
        entry.insert(0, placeholder)
        entry.grid(row=row + 1, column=0, columnspan=2, sticky="ew", ipady=8, pady=(0, 14))

        if focus:
            entry.focus_set()
            entry.delete(0, "end")

        return entry

    def _attempt_connect(self):
        username = self._username.get().strip()
        host     = self._host.get().strip()
        proto    = self._protocol.get()

        try:
            tcp_port = int(self._tcp_port.get().strip())
            udp_port = int(self._udp_port.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Port numbers should be valid.")
            return

        if not username:
            messagebox.showerror("Hata", "Username cannot be empty.")
            return

        if not host:
            messagebox.showerror("Hata", "Host address cannot be empty.")
            return

        self.on_connect(username, proto, host, tcp_port, udp_port)
