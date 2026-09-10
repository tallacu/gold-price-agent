from flask import Flask, jsonify, request
import os
import re
import requests
from datetime import datetime

app = Flask(__name__)

BALE_TOKEN = os.environ.get("BALE_TOKEN", "")

latest_prices = {
    "gold18": None,
    "mazaneh": None,
    "ounce": None,
    "dollar": None,
    "updated": None
}


def fa_to_en(text):
    if not text:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )
    return text.translate(table)


def clean_number(value):
    value = fa_to_en(value)
    value = value.replace(",", "")
    value = value.replace("٬", "")
    value = value.replace(" ", "")
    return float(value)


def extract_prices(text):
    text = fa_to_en(text)

    result = {
        "gold18": None,
        "mazaneh": None,
        "ounce": None,
        "dollar": None
    }

    # گرم ۱۸ تهران
    m = re.search(
        r"گرم\s*۱۸[^:\d]*[:：]?\s*([\d,٬]+)",
        text
    )
    if m:
        result["gold18"] = clean_number(m.group(1))

    # مظنه تهران
    m = re.search(
        r"مظنه\s*تهران[^:\d]*[:：]?\s*([\d,٬]+)",
        text
    )
    if m:
        result["mazaneh"] = clean_number(m.group(1))

    # انس طلا
    m = re.search(
        r"انس\s*طلا[^:\d]*[:：]?\s*([\d,.٬]+)",
        text
    )
    if m:
        result["ounce"] = clean_number(m.group(1))

    # دلار
    m = re.search(
        r"دلار[^:\d]*[:：]?\s*([\d,٬]+)",
        text
    )
    if m:
        result["dollar"] = clean_number(m.group(1))

    return result


def get_bale_updates():
    if not BALE_TOKEN:
        return []

    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates"

    try:
        response = requests.get(
            url,
            params={
                "limit": 20,
                "timeout": 0
            },
            timeout=15
        )

        data = response.json()

        if data.get("ok"):
            return data.get("result", [])

    except Exception as e:
        print("Bale error:", e)

    return []


def process_updates():
    global latest_prices

    updates = get_bale_updates()

    for update in updates:
        message = update.get("message", {})

        text = message.get("text", "")

        if not text:
            continue

        prices = extract_prices(text)

        # فقط پیام‌هایی که اطلاعات قیمت دارند قبول شود
        if prices["gold18"] is not None:

            for key in prices:
                if prices[key] is not None:
                    latest_prices[key] = prices[key]

            latest_prices["updated"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    return latest_prices


@app.route("/")
def home():
    return """
    <html lang="fa" dir="rtl">
    <meta charset="UTF-8">

    <body style="font-family:Arial;padding:30px">

    <h2>واسطه قیمت طلا فعال است</h2>

    <p>
    این سرویس پیام قیمت را از ربات بله دریافت می‌کند
    و برای اپلیکیشن ارسال می‌کند.
    </p>

    <p>
    API:
    <b>/api/prices</b>
    </p>

    </body>
    </html>
    """


@app.route("/api/prices")
def prices_api():

    process_updates()

    return jsonify({
        "ok": True,
        "prices": latest_prices
    })


@app.route("/test", methods=["POST"])
def test():

    data = request.get_json(silent=True) or {}

    text = data.get("text", "")

    prices = extract_prices(text)

    return jsonify({
        "ok": True,
        "prices": prices
    })


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
