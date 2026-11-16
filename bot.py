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

def send_market_signal(chat_id):
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AshkanAITrader/1.0"}
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode())

        if data.get("error"):
            raise RuntimeError(str(data["error"]))

        result = data["result"]
        pair = next(key for key in result if key != "last")

        candles = result[pair]
        closes = [float(candle[4]) for candle in candles[:-1]]

        if len(closes) < 40:
            raise RuntimeError("Not enough market data")

        def ema(values, period):
            alpha = 2 / (period + 1)
            value = sum(values[:period]) / period

            for price in values[period:]:
                value = price * alpha + value * (1 - alpha)

            return value

        changes = [
            closes[i] - closes[i - 1]
            for i in range(1, len(closes))
        ]

        gains = [max(x, 0) for x in changes[-14:]]
        losses = [max(-x, 0) for x in changes[-14:]]

        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14

        if avg_loss == 0:
            rsi = 100
        else:
            rsi = 100 - (100 / (1 + avg_gain / avg_loss))

        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)

        previous_macd = ema12 - ema26

        macd = previous_macd

        price = closes[-1]

        if macd > 0 and rsi > 50:
            signal = "روند صعودی 📈"
        elif macd < 0 and rsi < 50:
            signal = "روند نزولی 📉"
        else:
            signal = "بازار خنثی ⚖️"

        message = (
            "📊 ASHKAN AI TRADER\n\n"
            "🪙 BTC/USD\n"
            f"💰 قیمت: {price:,.2f} دلار\n"
            f"📈 RSI: {rsi:.2f}\n"
            f"📉 MACD: {macd:.2f}\n\n"
            f"🔎 وضعیت بازار: {signal}\n\n"
            "⚠️ تحلیل آزمایشی است و توصیه معاملاتی نیست."
        )

        send_message(chat_id, message)

    except Exception as e:
        print("Signal Error:", str(e))
        send_message(
            chat_id,
            "❌ دریافت اطلاعات بازار ناموفق بود. لطفاً بعداً تلاش کن."
        )
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
    send_market_signal(chat_id)

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
