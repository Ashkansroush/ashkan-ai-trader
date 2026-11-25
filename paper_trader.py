import json
import os
import threading

DATA_FILE = "paper_account.json"
LOCK = threading.RLock()

STARTING_BALANCE = 1000.0
RISK_PERCENT = 0.01


def load_account():
    if not os.path.exists(DATA_FILE):
        return {
            "balance": STARTING_BALANCE,
            "position": None,
            "trades": []
        }

    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_account(account):
    with open(DATA_FILE, "w") as file:
        json.dump(account, file, indent=4)


def get_account():
    with LOCK:
        return load_account()


def open_trade(price, stop_loss, take_profit):
    with LOCK:
        account = load_account()

        if account["position"] is not None:
            return "❌ یک معامله از قبل باز است."

        if price <= 0 or stop_loss <= 0 or take_profit <= 0:
            return "❌ قیمت‌ها باید مثبت باشند."

        if not stop_loss < price < take_profit:
            return "❌ حد ضرر و حد سود معتبر نیستند."

        risk_amount = account["balance"] * RISK_PERCENT
        risk_per_btc = price - stop_loss

        quantity = risk_amount / risk_per_btc
        cost = quantity * price

        if cost > account["balance"]:
            return "❌ موجودی برای این معامله کافی نیست."

        account["position"] = {
            "entry_price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "quantity": quantity,
            "risk_amount": risk_amount
        }

        save_account(account)

        return "✅ معامله آزمایشی خرید باز شد."


def close_trade(price, reason="manual"):
    with LOCK:
        account = load_account()
        position = account["position"]

        if position is None:
            return "❌ معامله بازی وجود ندارد."

        if price <= 0:
            return "❌ قیمت نامعتبر است."

        profit = (
            price - position["entry_price"]
        ) * position["quantity"]

        account["balance"] += profit

        account["trades"].append({
            "entry": position["entry_price"],
            "exit": price,
            "quantity": position["quantity"],
            "profit": profit,
            "reason": reason
        })

        account["position"] = None

        save_account(account)

        return (
            "✅ معامله بسته شد.\n"
            f"سود/زیان: {profit:.2f} دلار\n"
            f"موجودی: {account['balance']:.2f} دلار"
        )


def check_position(price):
    with LOCK:
        account = load_account()
        position = account["position"]

        if position is None:
            return None

        if price <= position["stop_loss"]:
            return close_trade(price, "stop_loss")

        if price >= position["take_profit"]:
            return close_trade(price, "take_profit")

        return None
