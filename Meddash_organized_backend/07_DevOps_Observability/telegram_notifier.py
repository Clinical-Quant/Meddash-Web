"""
telegram_notifier.py
====================
ClinicalQuant Ops — Core Telegram Alert Module

This is the central notification hub for the entire Antigravity ecosystem.
Any script (backup, crawler, etc.) can:
  A) Import this module and call send_alert() in Python, OR
  B) Call it from PowerShell/CMD as:
     python telegram_notifier.py --message "Your message" --level success

SETUP (One-Time):
1. Get your BOT_TOKEN from @BotFather on Telegram.
2. Get your CHAT_ID by messaging your bot, then visiting:
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
3. Paste both values below.
"""

import sys
import argparse
import datetime

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Run: python -m pip install requests")
    sys.exit(1)

# ============================================================
# CONFIGURATION — Fill these in once, then never touch again.
# ============================================================
BOT_TOKEN = "8714680243:AAF3fkuBzVSGK6eNByVC69Vy233TqxrNFuQ"
CHAT_ID   = "6253013213"
# ============================================================


def send_alert(message: str, level: str = "info") -> bool:
    """
    Sends a Telegram message to the configured CHAT_ID.

    Args:
        message (str): The body of the message to send.
        level (str):   'info', 'success', 'warning', or 'error'.

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    icons = {
        "info":    "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error":   "🚨",
    }
    icon = icons.get(level, "ℹ️")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = f"{icon} *ClinicalQuant Ops*\n`{timestamp}`\n\n{message}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": full_message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print(f"[Telegram] Alert sent: {level.upper()}")
            return True
        else:
            print(f"[Telegram] ERROR — Status {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[Telegram] CONNECTION ERROR: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClinicalQuant Ops Telegram Notifier")
    parser.add_argument("--message", type=str, help="Message to send", default=None)
    parser.add_argument("--level", type=str, default="info",
                        choices=["info", "success", "warning", "error"],
                        help="Alert level: info, success, warning, error")
    args = parser.parse_args()

    if args.message:
        # Called from PowerShell or CLI with --message argument
        success = send_alert(args.message, args.level)
        sys.exit(0 if success else 1)
    else:
        # No args — run the self-test
        print("No --message provided. Running connection test...")
        success = send_alert(
            "Bot is online and connected!\n\nThe ClinicalQuant Ops notification system is fully active. You will now receive alerts for backups and crawl completions.",
            level="success"
        )
        if success:
            print("SUCCESS! Check your Telegram app.")
        else:
            print("FAILED. Check your BOT_TOKEN and CHAT_ID in the script.")
