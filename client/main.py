# ─────────────────────────────────────────────
#  client/main.py  –  Giriş Noktası
# ─────────────────────────────────────────────

import sys
import os
sys.dont_write_bytecode = True

# Proje kökünü Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.app import App


if __name__ == "__main__":
    app = App()
    app.run()
