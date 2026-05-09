# ─────────────────────────────────────────────
#  gui/user_list.py  –  Online Kullanıcılar Paneli
# ─────────────────────────────────────────────

import tkinter as tk
from . import theme as T


class UserListPanel(tk.Frame):
    """Sol sidebar: online kullanıcıları gösterir."""

    def __init__(self, master, on_pm_click):
        """
        on_pm_click : callable(username) – kullanıcıya tıklanınca çağrılır
        """
        super().__init__(master, bg=T.BG_PANEL, width=T.SIDEBAR_W)
        self.on_pm_click = on_pm_click
        self._users      = []
        self._build()

    def _build(self):
        self.pack_propagate(False)

        # Başlık
        header = tk.Frame(self, bg=T.BG_PANEL, pady=0)
        header.pack(fill="x", padx=12, pady=(16, 8))

        tk.Label(
            header, text="ONLINE", font=("Consolas", 9, "bold"),
            fg=T.TEXT_SECONDARY, bg=T.BG_PANEL
        ).pack(side="left")

        self._count_lbl = tk.Label(
            header, text="0", font=("Consolas", 9, "bold"),
            fg=T.SUCCESS, bg=T.BG_PANEL
        )
        self._count_lbl.pack(side="right")

        # Ayırıcı
        sep = tk.Frame(self, bg=T.BORDER, height=1)
        sep.pack(fill="x")

        # Kaydırılabilir kullanıcı listesi
        self._list_frame = tk.Frame(self, bg=T.BG_PANEL)
        self._list_frame.pack(fill="both", expand=True, pady=8)

    def update_users(self, users: list, own_username: str = ""):
        """Kullanıcı listesini yeniden çizer."""
        self._users = users

        # Mevcut widget'ları temizle
        for w in self._list_frame.winfo_children():
            w.destroy()

        self._count_lbl.config(text=str(len(users)))

        for user_str in users:
            # Format: "Ad[TCP]"  veya  "Ad[UDP]"
            name, proto, color = self._parse_user(user_str)
            self._add_user_row(name, proto, color, is_self=(name == own_username))

    def _parse_user(self, user_str: str):
        """'Ad[TCP]' → (ad, 'TCP', renk)"""
        import re
        m = re.match(r"^(.+?)\[(\w+)\]$", user_str)
        if m:
            name  = m.group(1)
            proto = m.group(2)
            color = T.ACCENT_TCP if proto == "TCP" else T.ACCENT_UDP
            return name, proto, color
        return user_str, "", T.TEXT_SECONDARY

    def _add_user_row(self, name: str, proto: str, color: str, is_self: bool):
        row = tk.Frame(self._list_frame, bg=T.BG_PANEL, cursor="hand2")
        row.pack(fill="x", padx=8, pady=1)

        # Online nokta
        dot = tk.Label(row, text="●", font=("Consolas", 8),
                       fg=T.SUCCESS, bg=T.BG_PANEL)
        dot.pack(side="left", padx=(4, 6))

        # Kullanıcı adı
        lbl = tk.Label(
            row,
            text=name + (" (siz)" if is_self else ""),
            font=T.FONT_UI_S,
            fg=T.TEXT_PRIMARY if not is_self else T.TEXT_SECONDARY,
            bg=T.BG_PANEL,
            anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True)

        # Protokol etiketi
        if proto:
            pk = tk.Label(row, text=proto, font=("Consolas", 7, "bold"),
                          fg=color, bg=T.BG_PANEL)
            pk.pack(side="right", padx=(0, 6))

        # PM tıklama (kendi kendine değil)
        if not is_self:
            for widget in (row, dot, lbl):
                widget.bind("<Button-1>", lambda e, n=name: self.on_pm_click(n))
                widget.bind("<Enter>",    lambda e, r=row: r.config(bg=T.BG_HOVER))
                widget.bind("<Leave>",    lambda e, r=row: r.config(bg=T.BG_PANEL))
