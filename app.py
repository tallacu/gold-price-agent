from flask import Flask, jsonify
import os
import re
import json
import requests
from datetime import datetime

app = Flask(__name__)

# توکن فقط از Environment Variable خوانده می‌شود
BALE_TOKEN = os.environ.get("BALE_TOKEN", "")

# آخرین قیمت‌های دریافت‌شده
latest_prices = {
    "gold18": None,
    "mazaneh": None,
    "ounce": None,
    "dollar": None,
    "updated": None
}

# آخرین update که پردازش شده
last_update_id = 0


# --------------------------------------------------
# تبدیل اعداد فارسی و عربی به انگلیسی
# --------------------------------------------------

def fa_to_en(text):
    if not text:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(table)


# --------------------------------------------------
# تمیز کردن عدد
# --------------------------------------------------

def clean_number(value):
    value = fa_to_en(value)

    value = value.replace(",", "")
    value = value.replace("٬", "")
    value = value.replace(" ", "")

    try:
        return float(value)
    except:
        return None


# --------------------------------------------------
# استخراج قیمت‌ها از پیام
# --------------------------------------------------

def extract_prices(text):

    text = fa_to_en(text)

    result = {
        "gold18": None,
        "mazaneh": None,
        "ounce": None,
        "dollar": None
    }

    # -----------------------------
    # گرم ۱۸ تهران
    # -----------------------------

    patterns_gold18 = [
        r"گرم\s*۱۸\s*تهران\s*[:：]?\s*([\d,٬]+)",
        r"گرم\s*18\s*تهران\s*[:：]?\s*([\d,٬]+)"
    ]

    for pattern in patterns_gold18:

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            result["gold18"] = clean_number(match.group(1))
            break

    # -----------------------------
    # مظنه تهران
    # -----------------------------

    patterns_mazaneh = [
        r"مظنه\s*تهران\s*[:：]?\s*([\d,٬]+)",
        r"مظنه\s*[:：]?\s*([\d,٬]+)"
    ]

    for pattern in patterns_mazaneh:

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            result["mazaneh"] = clean_number(match.group(1))
            break

    # -----------------------------
    # انس طلا
    # -----------------------------

    patterns_ounce = [
        r"انس\s*طلا\s*[:：]?\s*([\d,.٬]+)",
        r"انس\s*[:：]?\s*([\d,.٬]+)"
    ]

    for pattern in patterns_ounce:

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            result["ounce"] = clean_number(match.group(1))
            break

    # -----------------------------
    # دلار
    # -----------------------------

    patterns_dollar = [
        r"دلار\s*[:：]?\s*([\d,٬]+)"
    ]

    for pattern in patterns_dollar:

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            result["dollar"] = clean_number(match.group(1))
            break

    return result


# --------------------------------------------------
# دریافت پیام‌های بله
# --------------------------------------------------

def get_bale_updates():

    if not BALE_TOKEN:
        print("ERROR: BALE_TOKEN is not set")
        return []

    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates"

    try:

        response = requests.get(
            url,
            params={
                "offset": last_update_id + 1,
                "limit": 100,
                "timeout": 0
            },
            timeout=20
        )

        print("Bale HTTP:", response.status_code)

        data = response.json()

        print("Bale OK:", data.get("ok"))

        if data.get("ok"):

            return data.get("result", [])

        print("Bale response:", data)

    except Exception as e:

        print("Bale ERROR:", str(e))

    return []


# --------------------------------------------------
# پردازش پیام‌ها
# --------------------------------------------------

def process_updates():

    global latest_prices
    global last_update_id

    updates = get_bale_updates()

    if not updates:

        return latest_prices

    # از قدیمی به جدید
    updates = sorted(
        updates,
        key=lambda x: x.get("update_id", 0)
    )

    for update in updates:

        update_id = update.get("update_id", 0)

        if update_id > last_update_id:
            last_update_id = update_id

        # ------------------------------------------
        # پیام معمولی
        # ------------------------------------------

        message = update.get("message", {})

        text = message.get("text", "")

        # ------------------------------------------
        # اگر پیام عکس/فایل با Caption بود
        # ------------------------------------------

        if not text:

            text = message.get("caption", "")

        if not text:
            continue

        print("MESSAGE RECEIVED:")
        print(text)

        prices = extract_prices(text)

        print("EXTRACTED:")
        print(prices)

        # ------------------------------------------
        # اگر حداقل قیمت ۱۸ وجود داشت
        # ------------------------------------------

        if prices["gold18"] is not None:

            if prices["gold18"] is not None:
                latest_prices["gold18"] = prices["gold18"]

            if prices["mazaneh"] is not None:
                latest_prices["mazaneh"] = prices["mazaneh"]

            if prices["ounce"] is not None:
                latest_prices["ounce"] = prices["ounce"]

            if prices["dollar"] is not None:
                latest_prices["dollar"] = prices["dollar"]

            latest_prices["updated"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            print("PRICE UPDATED!")

    return latest_prices


# --------------------------------------------------
# صفحه اصلی
# --------------------------------------------------

@app.route("/")
def home():

    return """
    <!DOCTYPE html>

    <html lang="fa" dir="rtl">

    <head>

        <meta charset="UTF-8">

        <title>واسطه قیمت طلا</title>

        <style>

            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 40px;
                background: #f5f5f5;
            }

            .box {
                max-width: 500px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            }

            h2 {
                margin-top: 0;
            }

        </style>

    </head>

    <body>

        <div class="box">

            <h2>واسطه قیمت طلا فعال است</h2>

            <p>
                سرویس آماده دریافت قیمت از ربات بله است.
            </p>

            <p>
                API:
                <br>
                <b>/api/prices</b>
            </p>

        </div>

    </body>

    </html>
    """


# --------------------------------------------------
# API قیمت‌ها
# --------------------------------------------------

@app.route("/api/prices")
def prices_api():

    prices = process_updates()

    return jsonify({
        "ok": True,
        "prices": prices
    })


# --------------------------------------------------
# تست استخراج متن
# --------------------------------------------------

@app.route("/test-message")
def test_message():

    sample = """
    تابان گوهر نفیس
    آخرین بروزرسانی: ۸:۳۰ ۱۹ شهریور ۱۴۰۵
    گرم ۱۸ تهران: ۲۴,۷۲۹,۰۰۰ تومان
    خرید متفرقه: ۲۴,۲۳۴,۰۰۰ تومان
    انس طلا: ۴,۴۰۸ دلار
    یک گرم طلای ۲۴ عیار: ۳۲,۹۷۲,۰۰۰ تومان
    مظنه تهران: ۱۰۷,۱۲۰ تومان
    دلار: ۲۳۵,۲۰۰ تومان
    """

    prices = extract_prices(sample)

    return jsonify({
        "ok": True,
        "sample": prices
    })


# --------------------------------------------------
# اجرای برنامه
# --------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
