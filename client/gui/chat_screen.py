# ─────────────────────────────────────────────
#  gui/chat_screen.py  –  Ana Sohbet Ekranı
# ─────────────────────────────────────────────

import tkinter as tk
from tkinter import scrolledtext
from .user_list import UserListPanel
from . import theme as T


class ChatScreen(tk.Frame):
    """
    Ana sohbet arayüzü:
    - Sol: online kullanıcı listesi
    - Orta: mesaj alanı (renkli)
    - Alt: input + gönder + disconnect
    """

    def __init__(self, master, username: str, protocol: str,
                 on_send, on_disconnect):
        super().__init__(master, bg=T.BG_DARK)
        self.username     = username
        self.protocol     = protocol
        self.on_send      = on_send
        self.on_disconnect = on_disconnect
        self._build()

    def _build(self):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Top bar ──────────────────────────────────────────
        topbar = tk.Frame(self, bg=T.BG_PANEL, height=48)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(
            topbar, text="◈  TCHAT", font=("Consolas", 13, "bold"),
            fg=T.ACCENT, bg=T.BG_PANEL
        ).pack(side="left", padx=18, pady=10)

        # Protokol badge
        proto_color = T.ACCENT_TCP if self.protocol == "TCP" else T.ACCENT_UDP
        tk.Label(
            topbar,
            text=f" {self.protocol} ",
            font=("Consolas", 9, "bold"),
            fg=T.BG_DARK, bg=proto_color,
        ).pack(side="left", pady=14)

        # Kullanıcı adı
        tk.Label(
            topbar, text=f"@{self.username}",
            font=T.FONT_UI_S, fg=T.TEXT_SECONDARY, bg=T.BG_PANEL
        ).pack(side="left", padx=10)

        # Durum göstergesi
        self._status_lbl = tk.Label(
            topbar, text="● Bağlı",
            font=T.FONT_UI_S, fg=T.SUCCESS, bg=T.BG_PANEL
        )
        self._status_lbl.pack(side="right", padx=18)

        # Disconnect butonu
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

        # Ayırıcı
        tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x", side="top")

        # ── Ana içerik: sidebar + mesaj alanı ────────────────
        content = tk.Frame(self, bg=T.BG_DARK)
        content.pack(fill="both", expand=True, side="top")

        # Sol sidebar
        self._user_panel = UserListPanel(content, on_pm_click=self._insert_pm)
        self._user_panel.pack(side="left", fill="y")

        # Dikey ayırıcı
        tk.Frame(content, bg=T.BORDER, width=1).pack(side="left", fill="y")

        # Mesaj alanı container
        msg_container = tk.Frame(content, bg=T.BG_DARK)
        msg_container.pack(side="left", fill="both", expand=True)

        # ScrolledText mesaj alanı
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
            state="disabled",
            cursor="arrow",
        )
        self._msg_area.pack(fill="both", expand=True, padx=0, pady=0)

        # Scrollbar
        scrollbar = tk.Scrollbar(
            msg_container, orient="vertical",
            command=self._msg_area.yview,
            bg=T.SCROLLBAR_BG, troughcolor=T.SCROLLBAR_BG,
            activebackground=T.SCROLLBAR_FG
        )
        self._msg_area.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Tag renkleri
        self._configure_tags()

        # ── Alt input çubuğu ─────────────────────────────────
        tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x", side="top")

        input_bar = tk.Frame(self, bg=T.BG_PANEL, height=T.INPUT_H)
        input_bar.pack(fill="x", side="bottom")
        input_bar.pack_propagate(False)

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

        # PM ipucu
        self._pm_hint = tk.Label(
            input_bar, text="",
            font=T.FONT_SMALL, fg=T.ACCENT_PM, bg=T.BG_PANEL
        )
        self._pm_hint.pack(side="left", padx=(0, 6))
        self._input.bind("<KeyRelease>", self._update_pm_hint)

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

    # ── Tag renkleri ─────────────────────────────────────────

    def _configure_tags(self):
        a = self._msg_area
        a.tag_config("ts",       foreground=T.TEXT_MUTED,    font=("Consolas", 9))
        a.tag_config("sender",   foreground=T.ACCENT,        font=("Consolas", 11, "bold"))
        a.tag_config("self",     foreground=T.SUCCESS,       font=("Consolas", 11, "bold"))
        a.tag_config("tcp",      foreground=T.ACCENT_TCP,    font=("Consolas", 9, "bold"))
        a.tag_config("udp",      foreground=T.ACCENT_UDP,    font=("Consolas", 9, "bold"))
        a.tag_config("body",     foreground=T.TEXT_PRIMARY,  font=T.FONT_MONO)
        a.tag_config("system",   foreground=T.TEXT_SECONDARY,font=("Consolas", 10, "italic"))
        a.tag_config("join",     foreground=T.SUCCESS,       font=("Consolas", 10, "italic"))
        a.tag_config("leave",    foreground=T.DANGER,        font=("Consolas", 10, "italic"))
        a.tag_config("pm_in",    foreground=T.ACCENT_PM,     font=("Consolas", 11, "bold"))
        a.tag_config("pm_body",  foreground=T.ACCENT_PM,     font=T.FONT_MONO)
        a.tag_config("divider",  foreground=T.TEXT_MUTED,    font=("Consolas", 8))

    # ── Mesaj ekleme ─────────────────────────────────────────

    def append_message(self, parsed: dict):
        """parse edilmiş mesaj sözlüğünü ekranda göster."""
        self._msg_area.config(state="normal")

        mtype = parsed.get("type", "system")

        if mtype == "chat":
            self._append_chat(parsed)
        elif mtype == "pm":
            self._append_pm(parsed)
        elif mtype in ("join", "leave"):
            self._append_event(parsed)
        elif mtype == "userlist":
            pass  # userlist sadece sidebar'da güncelleme yapar
        else:
            self._append_system(parsed)

        self._msg_area.config(state="disabled")
        self._msg_area.see("end")

    def _append_chat(self, p):
        is_self  = (p["sender"] == self.username)
        proto    = p.get("protocol", "")
        ts_text  = f" {p['ts']} "
        sender   = p["sender"]
        body     = p["body"]

        self._insert("ts",     ts_text)
        self._insert("self" if is_self else "sender", sender)
        self._insert("tcp" if proto == "TCP" else "udp", f"[{proto}] ")
        self._insert("body",   body + "\n")

    def _append_pm(self, p):
        is_outgoing = (p.get("sender", "") == self.username)  
        ts_text = f" {p['ts']} "
        label   = f"[PM → {p.get('target','')}]" if is_outgoing else f"[PM ← {p['sender']}]"

        self._insert("ts",     ts_text)
        self._insert("pm_in",  label + " ")
        self._insert("pm_body", p["body"] + "\n")

    def _append_event(self, p):
        symbol = "+" if p["type"] == "join" else "−"
        tag    = "join" if p["type"] == "join" else "leave"
        self._insert(tag, f" {p['ts']}  {symbol} {p['body']}\n")

    def _append_system(self, p):
        self._insert("system", f" {p['ts']}  ⓘ {p['body']}\n")

    def _insert(self, tag: str, text: str):
        self._msg_area.insert("end", text, tag)

    # ── Gönder ───────────────────────────────────────────────

    def _send(self):
        text = self._input.get().strip()
        if not text:
            return
        self._input.delete(0, "end")
        self._pm_hint.config(text="")
        self.on_send(text)

    # ── PM ipucu ─────────────────────────────────────────────

    def _update_pm_hint(self, event=None):
        text = self._input.get()
        if text.startswith("@") and " " not in text:
            self._pm_hint.config(text="PM: @kullanıcı mesaj")
        elif text.startswith("@") and " " in text:
            target = text.split(" ", 1)[0][1:]
            self._pm_hint.config(text=f"→ @{target}")
        else:
            self._pm_hint.config(text="")

    def _insert_pm(self, username: str):
        """Kullanıcı listesinden tıklanınca input'a @kullanıcı ekle."""
        current = self._input.get()
        if not current.startswith("@"):
            self._input.delete(0, "end")
            self._input.insert(0, f"@{username} ")
        self._input.focus_set()

    # ── Dışarıdan çağrılan metodlar ──────────────────────────

    def update_users(self, users: list):
        self._user_panel.update_users(users, own_username=self.username)

    def set_status(self, connected: bool):
        if connected:
            self._status_lbl.config(text="● Connected", fg=T.SUCCESS)
        else:
            self._status_lbl.config(text="● Disconnected", fg=T.DANGER)

    def set_disconnected_mode(self):
        """Bağlantı kesildikten sonra input'u kapat."""
        self._input.config(state="disabled")
        self.set_status(False)
