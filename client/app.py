# ─────────────────────────────────────────────
#  app.py  –  Ana Uygulama Kontrolcüsü
# ─────────────────────────────────────────────

import tkinter as tk
from tkinter import messagebox

from .gui.login_screen import LoginScreen
from .gui.chat_screen  import ChatScreen
from .gui              import theme as T
from .network.tcp_client import TCPClient
from .network.udp_client import UDPClient
from .utils.message      import detect_message_type, format_private_cmd, is_private, parse_private


class App:
    """
    Tkinter uygulamasının ana kontrolcüsü.
    Login → bağlantı kur → Chat ekranına geç.
    """

    def __init__(self):
        self.root = tk.Tk()
        self._online_users = []  # ["Merve[TCP]", "Serhat[TCP]", ...]
        self._setup_window()

        self.username : str       = ""
        self.protocol : str       = ""
        self._client  : object    = None  # TCPClient veya UDPClient
        self._chat    : ChatScreen = None

        # Ekranlar
        self._login_screen = LoginScreen(self.root, on_connect=self._on_login)

    # ── Pencere ayarları ─────────────────────────────────────

    def _setup_window(self):
        self.root.title("TChat")
        self.root.configure(bg=T.BG_DARK)
        self.root.geometry(f"{T.WIN_W}x{T.WIN_H}")
        self.root.minsize(700, 480)
        self.root.resizable(True, True)

        # İkonu gizle (varsa yükle)
        try:
            self.root.iconbitmap("assets/icon.ico")
        except Exception:
            pass

        # Kapatma davranışı
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Login ────────────────────────────────────────────────

    def _on_login(self, username: str, protocol: str,
              host: str, tcp_port: int, udp_port: int):
        self.username = username
        self.protocol = protocol

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

        # ── BURASI DEĞİŞTİ ──────────────────────────
        import threading

        def _connect():
            ok = self._client.connect()
            self.root.after(0, lambda: self._after_connect(ok))

        threading.Thread(target=_connect, daemon=True).start()
        # ────────────────────────────────────────────


    def _after_connect(self, ok: bool):
        if not ok:
            messagebox.showerror("Bağlantı Hatası", "Server'a bağlanılamadı.")
            return

        self._client.send(self.username)
        # Chat ekranını BURADA AÇMA, _process_message'da açacağız


    # ── Mesaj alma ───────────────────────────────────────────

    def _on_message(self, raw: str):
        """Network thread'inden gelen mesajı GUI thread'ine ilet."""
        self.root.after(0, self._process_message, raw)

    def _process_message(self, raw: str):
        if not self._chat:
            if "zaten sohbet odasinda" in raw:
                self._client.disconnect()
                self._client = None
                messagebox.showerror("Hata", "Bu kullanıcı adı zaten kullanımda!")
                return
            
            if "Hosgeldiniz" in raw and "baglisiniz" in raw:
                # Hoşgeldin mesajı geldi, şimdi chat ekranını aç
                self._login_screen.place_forget()
                self._chat = ChatScreen(
                    self.root,
                    username=self.username,
                    protocol=self.protocol,
                    on_send=self._on_send,
                    on_disconnect=self._on_user_disconnect
                )
                # Hoşgeldin mesajını chat'e yaz
                parsed = detect_message_type(raw)
                self._chat.append_message(parsed)
            return

        if "Kullanici adinizi giriniz" in raw:
            return

        parsed = detect_message_type(raw)
        if parsed["type"] == "userlist":
            self._online_users = parsed["users"]
            self._chat.update_users(parsed["users"])
            return

        self._chat.append_message(parsed)

    # ── Mesaj gönderme ───────────────────────────────────────

    def _on_send(self, text: str):
        if not self._client or not self._client.is_connected:
            return

        now = __import__("datetime").datetime.now().strftime("%H:%M")

        # Private mesaj mı?
        if is_private(text):
            target, body = parse_private(text)
    
            # Userlist'ten gerçek ismi bul (case-insensitive eşleştir)
            real_target = None
            for user_str in self._online_users:
                name = user_str.split("[")[0]
                if name.lower() == target.lower():
                    real_target = name
                    break

            if real_target is None:
                self._chat.append_message({
                    "type": "system",
                    "body": f"Kullanıcı bulunamadı: {target}",
                    "ts"  : __import__("datetime").datetime.now().strftime("%H:%M"),
                })
                return
            
            # Kendine PM engeli
            if target == self.username.lower():
                self._chat.append_message({
                    "type": "system",
                    "body": "Kendinize özel mesaj atamazsınız.",
                    "ts"  : __import__("datetime").datetime.now().strftime("%H:%M"),
                })
                return

            cmd = format_private_cmd(target, body)
            self._client.send(cmd)
            # Kendi ekranına göster (giden PM)
            self._chat.append_message({
                "type"    : "pm",
                "sender"  : self.username,
                "target"  : target,
                "protocol": self.protocol,
                "body"    : body,
                "ts"      : now,
            })
        else:
            self._client.send(text)
            # Kendi mesajını kendin ekrana ekle
            self._chat.append_message({
                "type"    : "chat",
                "sender"  : self.username,
                "protocol": self.protocol,
                "body"    : text,
                "ts"      : now,
            })
            

    # ── Bağlantı kesme ───────────────────────────────────────

    def _on_user_disconnect(self):
        """Kullanıcı 'AYRIL' butonuna bastı."""
        if self._client:
            # TCP için ayrılma mesajı server protokol akışıyla yönetiliyor;
            # socket kapanınca server zaten temizliyor.
            # UDP için "Gorusuruz" göndermek gerekiyor; disconnect() hallediyor.
            self._client.disconnect()
        self._return_to_login()

    def _on_disconnected(self):
        """Network thread: bağlantı koptu."""
        self.root.after(0, self._handle_disconnect)

    def _handle_disconnect(self):
        if self._chat:
            self._chat.set_disconnected_mode()
            self._chat.append_message({
                "type": "system",
                "body": "Bağlantı kesildi. Ana ekrana dönmek için AYRIL butonuna basın.",
                "ts"  : __import__("datetime").datetime.now().strftime("%H:%M"),
            })

    def _return_to_login(self):
        if self._chat:
            self._chat.place_forget()
            self._chat.destroy()
            self._chat = None
        self._client = None
        # Login ekranını yeniden oluştur
        self._login_screen = LoginScreen(self.root, on_connect=self._on_login)

    # ── Kapatma ──────────────────────────────────────────────

    def _on_close(self):
        if self._client:
            self._client.disconnect()
        self.root.destroy()

    # ── Çalıştır ─────────────────────────────────────────────

    def run(self):
        self.root.mainloop()
