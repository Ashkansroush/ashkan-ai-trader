import json
import urllib.request


# ASHKAN AI TRADER
# Market Analysis Engine
# Paper Trading Development

MARKETS = {
    "BTC": "XBTUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XRP": "XRPUSD",
    "DOGE": "XDGUSD"
}


def get_market_data(pair):

    url = (
        "https://api.kraken.com/0/public/OHLC"
        f"?pair={pair}&interval=60"
    )

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AshkanAITrader/1.0"}
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode())

    if data.get("error"):
        raise RuntimeError(str(data["error"]))

    result = data["result"]
    key = next(k for k in result if k != "last")

    candles = result[key]

    return [
        float(candle[4])
        for candle in candles[:-1]
    ]


def calculate_ema(values, period):

    if len(values) < period:
        raise ValueError("Not enough data")

    alpha = 2 / (period + 1)

    current = sum(values[:period]) / period
    output = [None] * (period - 1)
    output.append(current)

    for price in values[period:]:
        current = (
            price * alpha
            + current * (1 - alpha)
        )
        output.append(current)

    return output


def calculate_rsi(values, period=14):

    changes = [
        values[i] - values[i - 1]
        for i in range(1, len(values))
    ]

    if len(changes) < period:
        raise ValueError("Not enough data for RSI")

    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(changes)):
        avg_gain = (
            avg_gain * (period - 1) + gains[i]
        ) / period

        avg_loss = (
            avg_loss * (period - 1) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def analyze_market(symbol):

    if symbol not in MARKETS:
        raise ValueError("Unknown market")

    prices = get_market_data(MARKETS[symbol])

    if len(prices) < 60:
        raise ValueError("Insufficient market data")

    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)

    macd_values = [
        fast - slow
        for fast, slow in zip(ema12, ema26)
        if fast is not None and slow is not None
    ]

    signal_values = calculate_ema(macd_values, 9)

    macd = macd_values[-1]
    macd_signal = signal_values[-1]

    rsi = calculate_rsi(prices)

    price = prices[-1]

    if macd > macd_signal and rsi > 52:
        signal = "BUY"

    elif macd < macd_signal and rsi < 48:
        signal = "SELL"

    else:
        signal = "HOLD"

    return {
        "symbol": symbol,
        "price": price,
        "rsi": round(rsi, 2),
        "macd": round(macd, 4),
        "macd_signal": round(macd_signal, 4),
        "signal": signal
    }


def analyze_all_markets():

    results = []

    for symbol in MARKETS:

        try:
            result = analyze_market(symbol)
            results.append(result)

        except Exception as error:
            results.append({
                "symbol": symbol,
                "signal": "ERROR",
                "error": str(error)
            })

    return results
