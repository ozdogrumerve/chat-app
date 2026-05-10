# ◈ TChat

> A real-time, terminal-style chat application supporting both TCP and UDP protocols.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-FF6B6B?style=flat-square)
![TCP](https://img.shields.io/badge/TCP-12345-4f8ef7?style=flat-square)
![UDP](https://img.shields.io/badge/UDP-12346-f7a24f?style=flat-square)
![No Dependencies](https://img.shields.io/badge/dependencies-none-3ecf8e?style=flat-square)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.8+ |
| GUI | Tkinter |
| Networking | `socket` — TCP & UDP |
| Concurrency | `threading` |
| Message Parsing | `re` (regex) |
| No external packages | stdlib only |

---

## Features

- Simultaneous TCP and UDP client support
- Public chat room visible to all connected users
- Private messaging — type `@username message`
- Live online user list with protocol badge (TCP / UDP)
- Duplicate username prevention
- Dark, modern UI

---

## Getting Started

```bash
git clone https://github.com/user/tchat.git
cd tchat
```

No install step needed — zero external dependencies.

### 1. Start the server

```bash
python server/server.py
```

Listens on:
- TCP → `127.0.0.1:12345`
- UDP → `127.0.0.1:12346`

### 2. Start a client

```bash
python client/main.py
```

Pick a protocol, enter a username, hit **CONNECT**.

---

## Private Messages

Type in the message box:

```
@username hello there
```

Only the target user receives it. You can also click a username in the sidebar to auto-fill.

---

## Project Structure

```
tchat/
├── server/
│   └── server.py           # TCP + UDP hybrid server
├── client/
│   ├── main.py             # Entry point
│   ├── app.py              # Main app controller
│   ├── gui/
│   │   ├── chat_screen.py  # Chat UI
│   │   ├── login_screen.py # Login UI
│   │   ├── user_list.py    # Online users sidebar
│   │   └── theme.py        # Colors & fonts
│   ├── network/
│   │   ├── tcp_client.py   # TCP connection manager
│   │   └── udp_client.py   # UDP connection manager
│   └── utils/
│       └── message.py      # Message parser & formatter
└── requirements.txt
```

---

## TCP vs UDP

| | TCP | UDP |
|---|---|---|
| Connection | Connection-based | Connectionless |
| Reliability | High | Lower, but faster |
| Disconnect detection | Automatic | Manual (`Gorusuruz` signal) |
| Port | 12345 | 12346 |
