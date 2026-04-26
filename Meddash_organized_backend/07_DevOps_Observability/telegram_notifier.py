"""
telegram_notifier.py (v2.0 — MDP3-SWIP1)
==========================================
Meddash + ClinicalQuant Ops — Central Telegram Alert Module

Supports TWO bots:
  - CQ bot:    For ClinicalQuant newsletter pipeline alerts
  - Meddash bot: For Meddash engine + KOL pipeline alerts

Any script can:
  A) Import and call send_alert(message, level, channel)
  B) Call from CLI: python telegram_notifier.py --message "..." --level info --channel cq

SETUP:
1. Get BOT_TOKEN from @BotFather for each bot
2. Get CHAT_ID by messaging the bot, then visiting:
   https://api.telegram.org/bot<TOKEN>/getUpdates
3. Set env vars: CQ_TELEGRAM_BOT_TOKEN, CQ_TELEGRAM_CHAT_ID,
                  MEDDASH_TELEGRAM_BOT_TOKEN, MEDDASH_TELEGRAM_CHAT_ID
   Or edit the fallback defaults below.
"""

import os
import sys
import argparse
import datetime
import time
import logging

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Run: python -m pip install requests")
    sys.exit(1)

# ── Logging ────────────────────────────────────────────────────────────────
log = logging.getLogger("telegram_notifier")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)

# ══════════════════════════════════════════════════════════════════════════
# BOT CONFIGURATION
# Priority: Environment variables > Defaults below
# ══════════════════════════════════════════════════════════════════════════

BOTS = {
    "cq": {
        "token_env": "CQ_TELEGRAM_BOT_TOKEN",
        "chat_env": "CQ_TELEGRAM_CHAT_ID",
        "token_default": "871468...NFuQ",  # MDP3-SWIP1: existing CQ bot
        "chat_default": "6253013213",
        "prefix": "ClinicalQuant Ops",
    },
    "meddash": {
        "token_env": "MEDDASH_TELEGRAM_BOT_TOKEN",
        "chat_env": "MEDDASH_TELEGRAM_CHAT_ID",
        "token_default": "",  # MDP3-SWIP1: Dr. Don will create this bot
        "chat_default": "",
        "prefix": "Meddash Engine",
    },
}

# ── Rate Limiting ───────────────────────────────────────────────────────────
_last_sent = {}  # channel -> timestamp
MIN_INTERVAL = 2  # seconds between messages to same channel


def _get_bot_config(channel: str) -> dict:
    """Resolve bot config from env vars, falling back to defaults."""
    key = channel.lower()
    if key not in BOTS:
        log.warning(f"Unknown channel '{channel}', defaulting to 'cq'")
        key = "cq"
    cfg = BOTS[key]
    token = os.environ.get(cfg["token_env"], cfg["token_default"])
    chat_id = os.environ.get(cfg["chat_env"], cfg["chat_default"])
    return {"token": token, "chat_id": chat_id, "prefix": cfg["prefix"], "key": key}


def send_alert(message: str, level: str = "info", channel: str = "cq") -> bool:
    """
    Send a Telegram message to the configured channel.

    Args:
        message: The body of the message.
        level:   'info', 'success', 'warning', or 'error'.
        channel: 'cq' or 'meddash'. Falls back to 'cq' if unknown.

    Returns:
        True if sent successfully, False otherwise.
    """
    icons = {
        "info":    "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error":   "🚨",
    }
    icon = icons.get(level, "ℹ️")

    bot = _get_bot_config(channel)

    if not bot["token"] or not bot["chat_id"]:
        log.warning(f"[Telegram] {channel} bot not configured — token or chat_id empty. Skipping alert.")
        return False

    # ── Rate limiting ────────────────────────────────────────────────────
    now = time.time()
    last = _last_sent.get(channel, 0)
    if now - last < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - (now - last))
    _last_sent[channel] = time.time()

    # ── Build message ────────────────────────────────────────────────────
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    prefix = bot["prefix"]
    full_message = f"{icon} *{prefix}*\n`{timestamp}`\n\n{message}"

    url = f"https://api.telegram.org/bot{bot['token']}/sendMessage"
    payload = {
        "chat_id": bot["chat_id"],
        "text": full_message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            log.info(f"[Telegram] Alert sent: {level.upper()} → {channel}")
            return True
        else:
            log.error(f"[Telegram] HTTP {response.status_code}: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        log.error(f"[Telegram] Connection error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Meddash + ClinicalQuant Telegram Notifier (v2.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--message", type=str, help="Message to send", default=None)
    parser.add_argument("--level", type=str, default="info",
                        choices=["info", "success", "warning", "error"],
                        help="Alert level: info, success, warning, error")
    parser.add_argument("--channel", type=str, default="cq",
                        choices=["cq", "meddash"],
                        help="Bot channel: 'cq' for ClinicalQuant, 'meddash' for Meddash engine")
    args = parser.parse_args()

    if args.message:
        success = send_alert(args.message, args.level, args.channel)
        sys.exit(0 if success else 1)
    else:
        # Self-test mode
        print(f"Testing {args.channel} bot connection...")
        success = send_alert(
            f"Bot ({args.channel}) is online and connected!\n\n"
            f"The {args.channel.upper()} notification system is fully active.",
            level="success",
            channel=args.channel,
        )
        if success:
            print("SUCCESS! Check your Telegram app.")
        else:
            print(f"FAILED. Check your {args.channel.upper()} bot token and chat ID.")
        sys.exit(0 if success else 1)