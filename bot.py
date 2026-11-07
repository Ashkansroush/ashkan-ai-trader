import os
import json
import urllib.request
import urllib.parse
from flask import Flask, request, abort

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not WEBHOOK_SECRET:
    raise RuntimeError("WEBHOOK_SECRET is missing")

API = f"https://api.telegram.org/bot{TOKEN}/"

app = Flask(__name__)


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


def handle_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    command = message.get("text", "").strip()

    if not chat_id:
        return

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


@app.route("/")
def home():
    return "ASHKAN AI TRADER is running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != WEBHOOK_SECRET:
        abort(403)

    update = request.get_json(silent=True) or {}

    message = update.get("message", {})

    if message:
        handle_message(message)

    return {"ok": True}


def set_webhook():
    if not RENDER_URL:
        print("RENDER_EXTERNAL_URL is missing")
        return

    data = urllib.parse.urlencode({
        "url": RENDER_URL.rstrip("/") + "/webhook",
        "secret_token": WEBHOOK_SECRET
    }).encode()

    req = urllib.request.Request(
        API + "setWebhook",
        data=data
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        print("Webhook:", response.read().decode())


set_webhook()
