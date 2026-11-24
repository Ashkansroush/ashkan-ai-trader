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

    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode()


def get_market_data():
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

    # حذف کندل در حال تشکیل
    closes = [float(candle[4]) for candle in candles[:-1]]

    if len(closes) < 100:
        raise RuntimeError("Not enough market data")

    return closes


def ema_series(values, period):
    if len(values) < period:
        raise ValueError("Not enough values for EMA")

    alpha = 2 / (period + 1)

    current = sum(values[:period]) / period
    output = [None] * (period - 1) + [current]

    for price in values[period:]:
        current = price * alpha + current * (1 - alpha)
        output.append(current)

    return output


def calculate_rsi(closes, period=14):
    changes = [
        closes[i] - closes[i - 1]
        for i in range(1, len(closes))
    ]

    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (
            avg_gain * (period - 1) + gains[i]
        ) / period

        avg_loss = (
            avg_loss * (period - 1) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def calculate_macd(closes):
    ema12 = ema_series(closes, 12)
    ema26 = ema_series(closes, 26)

    macd_values = [
        fast - slow
        for fast, slow in zip(ema12, ema26)
        if fast is not None and slow is not None
    ]

    signal_values = ema_series(macd_values, 9)

    macd = macd_values[-1]
    signal = signal_values[-1]
    histogram = macd - signal

    return macd, signal, histogram


def analyze_market():
    closes = get_market_data()

    price = closes[-1]

    rsi = calculate_rsi(closes)

    macd, macd_signal, histogram = calculate_macd(closes)

    if histogram > 0 and rsi > 50:
        trend = "روند صعودی 📈"

    elif histogram < 0 and rsi < 50:
        trend = "روند نزولی 📉"

    else:
        trend = "بازار خنثی ⚖️"

    if rsi >= 70:
        rsi_status = "اشباع خرید"

    elif rsi <= 30:
        rsi_status = "اشباع فروش"

    else:
        rsi_status = "متعادل"

    return {
        "price": price,
        "rsi": rsi,
        "rsi_status": rsi_status,
        "macd": macd,
        "macd_signal": macd_signal,
        "histogram": histogram,
        "trend": trend
    }


def send_market_signal(chat_id):
    try:
        result = analyze_market()

        message = (
            "📊 ASHKAN AI TRADER\n\n"
            "🪙 BTC/USD\n"
            f"💰 قیمت: {result['price']:,.2f} دلار\n\n"
            f"📈 RSI: {result['rsi']:.2f}\n"
            f"🔎 وضعیت RSI: {result['rsi_status']}\n\n"
            f"📉 MACD: {result['macd']:.2f}\n"
            f"📊 MACD Signal: {result['macd_signal']:.2f}\n"
            f"📊 Histogram: {result['histogram']:.2f}\n\n"
            f"🔍 وضعیت بازار: {result['trend']}\n\n"
            "⚠️ این تحلیل آزمایشی است و توصیه معاملاتی نیست."
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
            "/signal - تحلیل بازار"
        )

    elif command == "/help":
        send_message(
            chat_id,
            "راهنمای ربات:\n"
            "/start - شروع\n"
            "/signal - تحلیل بازار"
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
