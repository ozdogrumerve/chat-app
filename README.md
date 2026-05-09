# TChat — TCP/UDP Chat Uygulaması

> Koyu & modern Tkinter arayüzlü, TCP ve UDP protokollerini aynı anda destekleyen Python sohbet uygulaması.

---

## ✨ Özellikler

| Özellik | Açıklama |
|---|---|
| **Dual-protocol** | TCP ve UDP istemcileri aynı anda aynı sunucuya bağlanabilir |
| **Zaman damgası** | Her mesajın yanında `HH:MM` formatında saat gösterilir |
| **Online kullanıcılar** | Sol panelde gerçek zamanlı olarak güncellenen kullanıcı listesi |
| **Private mesaj** | `@kullanıcı mesaj` yazarak özel mesaj gönderme |
| **Protokol etiketi** | Her mesajın yanında `[TCP]` veya `[UDP]` rozeti |
| **Bağlantı yönetimi** | Kopuk bağlantı tespiti, düzgün ayrılma protokolü |
| **Koyu tema** | `#0d0f14` tabanlı, vurgu renkleriyle modern arayüz |

---

## 📁 Proje Yapısı

```
chat-app/
├── README.md
├── requirements.txt
│
├── server/
│   └── server.py              # TCP + UDP hybrid server
│
└── client/
    ├── main.py                # Giriş noktası
    ├── app.py                 # Ana Tkinter kontrolcüsü
    │
    ├── network/
    │   ├── tcp_client.py      # TCP bağlantı yöneticisi
    │   └── udp_client.py      # UDP bağlantı yöneticisi
    │
    ├── gui/
    │   ├── login_screen.py    # Giriş ekranı
    │   ├── chat_screen.py     # Ana sohbet ekranı
    │   ├── user_list.py       # Online kullanıcılar paneli
    │   └── theme.py           # Renk, font, boyut sabitleri
    │
    └── utils/
        └── message.py         # Mesaj parse & format yardımcıları
```

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

- Python **3.8+**
- Tkinter (Python ile birlikte gelir; Linux'ta `sudo apt install python3-tk`)

### 1. Sunucuyu başlat

```bash
python server/server.py
```

### 2. İstemciyi başlat (istediğin kadar terminal aç)

```bash
python client/main.py
```

- Protokol seç: **TCP** veya **UDP**
- Host ve portları gir (varsayılan `127.0.0.1 / 12345 / 12346`)
- Kullanıcı adını gir → **BAĞLAN**

---

## 💬 Kullanım

| Eylem | Nasıl |
|---|---|
| Mesaj gönder | Input kutusuna yaz → Enter veya GÖNDER butonu |
| Private mesaj | `@kullanıcı mesaj içeriği` yaz |
| Kullanıcıya PM | Sol panelde kullanıcıya tıkla → input'a `@kullanıcı` otomatik eklenir |
| Odadan ayrıl | Sağ üstteki **AYRIL** butonu |

---

## 🏗️ Mimari

```
┌─────────────┐     TCP (12345)     ┌──────────────┐
│  TCP Client │ ─────────────────── │              │
└─────────────┘                     │    Server    │
                                    │              │
┌─────────────┐     UDP (12346)     │  (server.py) │
│  UDP Client │ ─────────────────── │              │
└─────────────┘                     └──────────────┘
```

**Server:** Her TCP istemcisi için ayrı thread. UDP mesajları da thread havuzunda işlenir. Tüm broadcast işlemleri `threading.Lock` ile thread-safe.

**Client:** GUI thread (Tkinter) ve network thread birbirinden ayrılmıştır. `root.after(0, ...)` ile thread-safe GUI güncellemesi yapılır.

---

## 📡 Protokol

### Sunucu → İstemci Mesaj Formatları

```
# Normal mesaj
KullaniciAdi[TCP] : mesaj içeriği

# Private mesaj
[PM|Hedef] Gonderen[TCP] : mesaj içeriği

# Katılım / ayrılış
KullaniciAdi - [TCP] ile sohbet odasina katildi.
KullaniciAdi - [UDP] sohbet odasindan ayrildi

# Kullanıcı listesi güncellemesi
/userlist Ad1[TCP],Ad2[UDP],Ad3[TCP]
```

### İstemci → Sunucu

```
# Normal mesaj
mesaj içeriği

# Private mesaj
/pm HedefKullanici mesaj içeriği

# UDP ayrılış
Gorusuruz
```

---

## 📄 Lisans

MIT
