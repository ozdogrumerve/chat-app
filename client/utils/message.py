# ─────────────────────────────────────────────
#  utils/message.py  –  Mesaj Parse & Format
# ─────────────────────────────────────────────

import re
from datetime import datetime


def timestamp() -> str:
    """Şu anki saati HH:MM formatında döndürür."""
    return datetime.now().strftime("%H:%M")


def is_private(message: str) -> bool:
    """Mesaj private komut mu? (@kullanici mesaj)"""
    return message.startswith("@") and " " in message


def parse_private(message: str):
    """'@hedef mesaj' → (hedef, mesaj) tuple döndürür."""
    parts = message.split(" ", 1)
    target = parts[0][1:]   # @ işaretini at
    body   = parts[1] if len(parts) > 1 else ""
    return target, body


def format_private_cmd(target: str, body: str) -> str:
    """Client → server private mesaj formatı."""
    return f"/pm {target} {body}"


def detect_message_type(raw: str):
    """
    Server'dan gelen ham mesajı parse eder.
    Dönüş: dict {type, sender, protocol, body, target, ts}
    type: 'join' | 'leave' | 'pm' | 'chat' | 'system' | 'userlist'
    """
    ts = timestamp()

    if raw.startswith("/prompt "):
        return None  # görmezden gel

    # Online kullanıcı listesi güncellemesi
    if raw.startswith("/userlist "):
        users_str = raw[len("/userlist "):]
        users = [u.strip() for u in users_str.split(",") if u.strip()]
        return {"type": "userlist", "users": users, "ts": ts}

    # Private mesaj bildirimi
    pm_match = re.match(r"^\[PM(?:\|(.+?))?\] (.+?)\[(\w+)\] : (.+)$", raw)
    if pm_match:
        return {
            "type"    : "pm",
            "target"  : pm_match.group(1) or "",
            "sender"  : pm_match.group(2),
            "protocol": pm_match.group(3),
            "body"    : pm_match.group(4),
            "ts"      : ts,
        }

    # Katılım mesajı
    join_match = re.match(r"^(.+) - \[(\w+)\] ile sohbet odasina katildi\.$", raw)
    if join_match:
        return {
            "type"    : "join",
            "sender"  : join_match.group(1),
            "protocol": join_match.group(2),
            "body"    : raw,
            "ts"      : ts,
        }

    # Ayrılma mesajı
    leave_match = re.match(r"^(.+) - \[(\w+)\] sohbet odasindan ayrildi$", raw)
    if leave_match:
        return {
            "type"    : "leave",
            "sender"  : leave_match.group(1),
            "protocol": leave_match.group(2),
            "body"    : raw,
            "ts"      : ts,
        }

    # Normal sohbet mesajı  →  "KullaniciAdi[TCP] : mesaj"
    chat_match = re.match(r"^(.+?)\[(\w+)\] : (.+)$", raw)
    if chat_match:
        return {
            "type"    : "chat",
            "sender"  : chat_match.group(1),
            "protocol": chat_match.group(2),
            "body"    : chat_match.group(3),
            "ts"      : ts,
        }

    # Sistem / bilgi mesajı (Hosgeldiniz, uyarılar vs.)
    return {"type": "system", "body": raw, "ts": ts}
