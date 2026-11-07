import os
import time
import json
import urllib.request
import urllib.parse

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

API = f"https://api.telegram.org/bot{TOKEN}/"

def send_message(chat_id, text):
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text
    }).encode()

    req = urllib.request.Request(
        API + "sendMessage",
        data=data
    )

    urllib.request.urlopen(req, timeout=30)

def main():
    offset = 0

    while True:
        try:
            url = API + "getUpdates?" + urllib.parse.urlencode({
                "offset": offset,
                "timeout": 25
            })

            with urllib.request.urlopen(url, timeout=35) as response:
                updates = json.loads(response.read())

            for update in updates.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message", {})
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                command = message.get("text", "").strip()

                if not chat_id:
                    continue

                if command == "/start":
                    send_message(
                        chat_id,
                        "سلام! به ASHKAN AI TRADER خوش اومدی 🤖\n\n"
                        "/help - راهنما\n"
                        "/signal - سیگنال آزمایشی"
                    )

                elif command == "/help":
                    send_message(
                        chat_id,
                        "راهنمای ربات:\n"
                        "/start - شروع\n"
                        "/signal - سیگنال آزمایشی"
                    )

                elif command == "/signal":
                    send_message(
                        chat_id,
                        "📊 بخش سیگنال آزمایشی\n\n"
                        "این نسخه هنوز به بازار متصل نیست.\n"
                        "هیچ سیگنال واقعی یا توصیه خرید و فروش صادر نمی‌شود."
                    )

                else:
                    send_message(
                        chat_id,
                        "دستور نامعتبر است. /help را بزن."
                    )

        except Exception as error:
            print("Error:", error)
            time.sleep(5)

if __name__ == "__main__":
    main()
