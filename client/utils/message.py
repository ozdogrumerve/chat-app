# ─────────────────────────────────────────────
#  utils/message.py  –  Message Parsing & Formatting
# ─────────────────────────────────────────────

import re
from datetime import datetime


def timestamp() -> str:
    """Return the current time as HH:MM string."""
    return datetime.now().strftime("%H:%M")


def is_private(message: str) -> bool:
    """Check if the message is a private message command (@username text)."""
    return message.startswith("@") and " " in message


def parse_private(message: str):
    """Parse '@username message' into a (target, body) tuple."""
    parts  = message.split(" ", 1)
    target = parts[0][1:]                        # strip the leading @
    body   = parts[1] if len(parts) > 1 else ""  # everything after the first space
    return target, body


def format_private_cmd(target: str, body: str) -> str:
    """Format a private message into the server command: /pm target body."""
    return f"/pm {target} {body}"


def detect_message_type(raw: str):
    """
    Parse a raw message string received from the server.
    Returns a dict with keys: type, sender, protocol, body, target, ts
    Possible types: 'join' | 'leave' | 'pm' | 'chat' | 'system' | 'userlist'
    """
    ts = timestamp()  # attach current time to every parsed message

    # Internal prompt messages from server — silently ignore
    if raw.startswith("/prompt "):
        return None

    # ── User list update ─────────────────────────────────
    # Format: "/userlist Name1[TCP],Name2[UDP],..."
    if raw.startswith("/userlist "):
        users_str = raw[len("/userlist "):]
        users = [u.strip() for u in users_str.split(",") if u.strip()]
        return {"type": "userlist", "users": users, "ts": ts}

    # ── Private message ──────────────────────────────────
    # Format: "[PM|target] Sender[TCP] : body"
    pm_match = re.match(r"^\[PM(?:\|(.+?))?\] (.+?)\[(\w+)\] : (.+)$", raw)
    if pm_match:
        return {
            "type"    : "pm",
            "target"  : pm_match.group(1) or "",  # recipient username
            "sender"  : pm_match.group(2),         # sender username
            "protocol": pm_match.group(3),         # TCP or UDP
            "body"    : pm_match.group(4),         # message content
            "ts"      : ts,
        }

    # ── Join event ───────────────────────────────────────
    # Format: "Username - [TCP] ile sohbet odasina katildi."
    join_match = re.match(r"^(.+) - \[(\w+)\] joined the chat room\.$", raw)
    if join_match:
        return {
            "type"    : "join",
            "sender"  : join_match.group(1),  # who joined
            "protocol": join_match.group(2),  # with which protocol
            "body"    : raw,                  # full raw string shown in chat
            "ts"      : ts,
        }

    # ── Leave event ──────────────────────────────────────
    # Format: "Username - [TCP] sohbet odasindan ayrildi"
    leave_match = re.match(r"^(.+) - \[(\w+)\] left the chat room$", raw)
    if leave_match:
        return {
            "type"    : "leave",
            "sender"  : leave_match.group(1),  # who left
            "protocol": leave_match.group(2),  # with which protocol
            "body"    : raw,                   # full raw string shown in chat
            "ts"      : ts,
        }

    # ── Public chat message ──────────────────────────────
    # Format: "Username[TCP] : message body"
    chat_match = re.match(r"^(.+?)\[(\w+)\] : (.+)$", raw)
    if chat_match:
        return {
            "type"    : "chat",
            "sender"  : chat_match.group(1),  # sender username
            "protocol": chat_match.group(2),  # TCP or UDP
            "body"    : chat_match.group(3),  # message content
            "ts"      : ts,
        }

    # ── System / info message ────────────────────────────
    # Fallback for anything that didn't match above (welcome messages, errors, etc.)
    return {"type": "system", "body": raw, "ts": ts}