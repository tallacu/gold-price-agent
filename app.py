from flask import Flask, jsonify
import os
import re
import requests
from datetime import datetime

app = Flask(__name__)

# =========================================================
# تنظیمات
# =========================================================

BALE_TOKEN = os.environ.get("BALE_TOKEN", "")

# قیمت‌های آخرین پیام
latest_prices = {
    "gold18": None,
    "mazaneh": None,
    "ounce": None,
    "dollar": None,
    "updated": None
}

# آخرین update دریافت‌شده از Bale
last_update_id = 0


# =========================================================
# تبدیل اعداد فارسی و عربی به انگلیسی
# =========================================================

def fa_to_en(text):
    if not text:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return str(text).translate(table)


# =========================================================
# تبدیل متن عددی به عدد
# =========================================================

def clean_number(value):
    if value is None:
        return None

    value = fa_to_en(value)

    value = value.replace(",", "")
    value = value.replace("٬", "")
    value = value.replace(" ", "")

    try:
        return float(value)
    except Exception:
        return None


# =========================================================
# استخراج قیمت‌ها از پیام Bale
# =========================================================

def extract_prices(text):

    text = fa_to_en(text)

    result = {
        "gold18": None,
        "mazaneh": None,
        "ounce": None,
        "dollar": None
    }

    # -----------------------------------------------------
    # گرم ۱۸ تهران
    # -----------------------------------------------------

    patterns_gold18 = [
        r"گرم\s*۱۸\s*تهران\s*[:：]?\s*([\d,٬]+)",
        r"گرم\s*18\s*تهران\s*[:：]?\s*([\d,٬]+)"
    ]

    for pattern in patterns_gold18:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            result["gold18"] = clean_number(match.group(1))
            break

    # -----------------------------------------------------
    # مظنه تهران
    # -----------------------------------------------------

    patterns_mazaneh = [
        r"مظنه\s*تهران\s*[:：]?\s*([\d,٬]+)",
        r"مظنه\s*[:：]?\s*([\d,٬]+)"
    ]

    for pattern in patterns_mazaneh:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            result["mazaneh"] = clean_number(match.group(1))
            break

    # -----------------------------------------------------
    # انس طلا
    # -----------------------------------------------------

    patterns_ounce = [
        r"انس\s*طلا\s*[:：]?\s*([\d,.٬]+)",
        r"انس\s*[:：]?\s*([\d,.٬]+)"
    ]

    for pattern in patterns_ounce:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            result["ounce"] = clean_number(match.group(1))
            break

    # -----------------------------------------------------
    # دلار
    # -----------------------------------------------------

    patterns_dollar = [
        r"دلار\s*[:：]?\s*([\d,٬]+)"
    ]

    for pattern in patterns_dollar:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            result["dollar"] = clean_number(match.group(1))
            break

    return result


# =========================================================
# دریافت Update از Bale
# =========================================================

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
                "limit": 100
            },
            timeout=8
        )

        print("Bale HTTP:", response.status_code)

        data = response.json()

        print("Bale OK:", data.get("ok"))

        if data.get("ok"):
            return data.get("result", [])

        print("Bale response:", data)

    except requests.exceptions.Timeout:

        print("Bale ERROR: timeout")

    except requests.exceptions.RequestException as e:

        print("Bale ERROR:", str(e))

    except Exception as e:

        print("Bale ERROR:", str(e))

    return []


# =========================================================
# پردازش پیام‌های Bale
# =========================================================

def process_updates():

    global last_update_id
    global latest_prices

    updates = get_bale_updates()

    if not updates:
        return latest_prices

    updates = sorted(
        updates,
        key=lambda x: x.get("update_id", 0)
    )

    for update in updates:

        update_id = update.get("update_id", 0)

        if update_id > last_update_id:
            last_update_id = update_id

        message = update.get("message", {})

        text = message.get("text", "")

        if not text:
            text = message.get("caption", "")

        if not text:
            continue

        print("--------------------------------")
        print("MESSAGE RECEIVED:")
        print(text)

        prices = extract_prices(text)

        print("EXTRACTED:")
        print(prices)

        # اگر حداقل قیمت طلای ۱۸ پیدا شد
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


# =========================================================
# CORS
# =========================================================

@app.after_request
def add_cors_headers(response):

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"

    response.headers["Cache-Control"] = "no-store"

    return response


# =========================================================
# صفحه اصلی
# =========================================================

@app.route("/")
def home():

    return """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Gold Price Agent</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #111827;
                color: white;
                text-align: center;
                padding: 50px;
            }

            h1 {
                color: #f5c542;
            }

            .box {
                max-width: 600px;
                margin: auto;
                padding: 25px;
                background: #1f2937;
                border-radius: 15px;
            }

            a {
                display: block;
                margin: 15px;
                padding: 15px;
                background: #374151;
                color: white;
                text-decoration: none;
                border-radius: 10px;
            }

            a:hover {
                background: #4b5563;
            }
        </style>
    </head>

    <body>

        <div class="box">

            <h1>Gold Price Agent</h1>

            <p>سرویس آنلاین قیمت طلا فعال است.</p>

            <a href="/api/health">
                تست سلامت سرویس
            </a>

            <a href="/api/prices">
                مشاهده قیمت ذخیره شده
            </a>

            <a href="/api/refresh">
                دریافت قیمت جدید از بله
            </a>

            <a href="/test-message">
                تست خواندن پیام
            </a>

        </div>

    </body>
    </html>
    """


# =========================================================
# Health Check
# این مسیر نباید به Bale وصل شود
# =========================================================

@app.route("/api/health")
def health():

    return jsonify({
        "ok": True,
        "service": "gold-price-agent",
        "status": "running"
    })


# =========================================================
# دریافت قیمت جدید از Bale
# =========================================================

@app.route("/api/refresh")
def refresh():

    try:

        prices = process_updates()

        return jsonify({
            "ok": True,
            "source": "bale",
            "prices": prices
        })

    except Exception as e:

        print("REFRESH ERROR:", str(e))

        return jsonify({
            "ok": False,
            "error": str(e),
            "prices": latest_prices
        }), 500


# =========================================================
# API اصلی قیمت
#
# این مسیر دیگر به Bale وصل نمی‌شود.
# فقط اطلاعات ذخیره‌شده را برمی‌گرداند.
# =========================================================

@app.route("/api/prices")
def prices_api():

    return jsonify({
        "ok": True,
        "prices": latest_prices
    })


# =========================================================
# تست Parser
# =========================================================

@app.route("/test-message")
def test_message():

    sample = """
تابان گوهر نفیس

آخرین بروزرسانی: ۸:۳۰ ۱۹ شهریور ۱۴۰۵

گرم ۱۸ تهران: ۲۴,۷۲۹,۰۰۰ تومان
خرید متفرقه: ۲۴,۲۳۴,۰۰۰ تومان
انس طلا: ۴,۴۰۸ دلار
یک گرم طلای ۲۴ عیار: ۳۲,۹۷۲,۰۰۰ تومان
یک گرم طلای ۲۰ عیار: ۲۷,۴۶۵,۰۰۰ تومان
یک گرم طلای ۲۱ عیار: ۲۸,۸۵۰,۰۰۰ تومان
مظنه تهران: ۱۰۷,۱۲۰ تومان
انس نقره: ۶۷.۴۵ دلار
دلار: ۲۳۵,۲۰۰ تومان
یورو: ۲۷۱,۷۴۰ تومان
درهم: ۶۴,۰۰۰ تومان
"""

    prices = extract_prices(sample)

    return jsonify({
        "ok": True,
        "sample": prices
    })


# =========================================================
# اجرای برنامه
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
