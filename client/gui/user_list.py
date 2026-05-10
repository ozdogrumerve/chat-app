# ─────────────────────────────────────────────
#  gui/user_list.py  –  Online Users Panel
# ─────────────────────────────────────────────

import tkinter as tk
from . import theme as T


class UserListPanel(tk.Frame):
    """Left sidebar panel that displays online users."""

    def __init__(self, master, on_pm_click):
        """
        on_pm_click : callable(username) — called when a user row is clicked
        """
        super().__init__(master, bg=T.BG_PANEL, width=T.SIDEBAR_W)
        self.on_pm_click = on_pm_click  # callback to auto-fill PM in input box
        self._users      = []           # current user list
        self._build()

    def _build(self):
        # Prevent the frame from shrinking to fit its children
        self.pack_propagate(False)

        # ── Header row: "ONLINE" label + user count ──────────
        header = tk.Frame(self, bg=T.BG_PANEL, pady=0)
        header.pack(fill="x", padx=12, pady=(16, 8))

        tk.Label(
            header, text="ONLINE", font=("Consolas", 9, "bold"),
            fg=T.TEXT_SECONDARY, bg=T.BG_PANEL
        ).pack(side="left")

        # Count label — updated dynamically when user list changes
        self._count_lbl = tk.Label(
            header, text="0", font=("Consolas", 9, "bold"),
            fg=T.SUCCESS, bg=T.BG_PANEL
        )
        self._count_lbl.pack(side="right")

        # Horizontal divider below the header
        sep = tk.Frame(self, bg=T.BORDER, height=1)
        sep.pack(fill="x")

        # Scrollable container for user rows
        self._list_frame = tk.Frame(self, bg=T.BG_PANEL)
        self._list_frame.pack(fill="both", expand=True, pady=8)

    def update_users(self, users: list, own_username: str = ""):
        """Clear and redraw the user list with the latest data."""
        self._users = users

        # Remove all existing user row widgets
        for w in self._list_frame.winfo_children():
            w.destroy()

        # Update the online count label
        self._count_lbl.config(text=str(len(users)))

        # Rebuild one row per user
        for user_str in users:
            # Expected format: "Name[TCP]" or "Name[UDP]"
            name, proto, color = self._parse_user(user_str)
            self._add_user_row(name, proto, color, is_self=(name == own_username))

    def _parse_user(self, user_str: str):
        """Parse 'Name[TCP]' into (name, protocol, color)."""
        import re
        m = re.match(r"^(.+?)\[(\w+)\]$", user_str)
        if m:
            name  = m.group(1)
            proto = m.group(2)
            color = T.ACCENT_TCP if proto == "TCP" else T.ACCENT_UDP
            return name, proto, color
        # Fallback if format doesn't match
        return user_str, "", T.TEXT_SECONDARY

    def _add_user_row(self, name: str, proto: str, color: str, is_self: bool):
        """Create and pack a single user row into the list frame."""

        # Row container — full width, hand cursor for clickability
        row = tk.Frame(self._list_frame, bg=T.BG_PANEL, cursor="hand2")
        row.pack(fill="x", padx=8, pady=1)

        # Green dot indicating the user is online
        dot = tk.Label(row, text="●", font=("Consolas", 8),
                       fg=T.SUCCESS, bg=T.BG_PANEL)
        dot.pack(side="left", padx=(4, 6))

        # Username label — dimmed and marked "(you)" for own entry
        lbl = tk.Label(
            row,
            text=name + (" (you)" if is_self else ""),
            font=T.FONT_UI_S,
            fg=T.TEXT_PRIMARY if not is_self else T.TEXT_SECONDARY,
            bg=T.BG_PANEL,
            anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True)

        # Protocol badge on the right (TCP or UDP)
        if proto:
            pk = tk.Label(row, text=proto, font=("Consolas", 7, "bold"),
                          fg=color, bg=T.BG_PANEL)
            pk.pack(side="right", padx=(0, 6))

        # Bind click and hover events — only for other users, not yourself
        if not is_self:
            for widget in (row, dot, lbl):
                # Click: auto-fill "@name " in the message input
                widget.bind("<Button-1>", lambda e, n=name: self.on_pm_click(n))
                # Hover highlight
                widget.bind("<Enter>",    lambda e, r=row: r.config(bg=T.BG_HOVER))
                widget.bind("<Leave>",    lambda e, r=row: r.config(bg=T.BG_PANEL))
                