import os
import requests
import time
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
users = set()
last_alert = None

# 🔹 Route عادي باش السيرفر ما يطيحش
@app.route("/")
def home():
    return "Bot is running ✅"

def get_gold_price():
    url = f"https://api.metals.dev/v1/latest?api_key={API_KEY}&base=USD"
    r = requests.get(url).json()
    return float(r["gold"])

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    global users
    data = request.json

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        users.add(chat_id)

        if text.lower() == "prix":
            try:
                price = get_gold_price()
                send_message(chat_id, f"💰 Gold price now: {price}$ per ounce")
            except:
                send_message(chat_id, "⚠️ Error getting gold price.")

    return "ok"

def check_price():
    global last_alert
    while True:
        try:
            price = get_gold_price()

            if price <= 2900 and last_alert != "down":
                for u in users:
                    send_message(u, "📉 Gold dropped!")
                last_alert = "down"

            elif price >= 3000 and last_alert != "up":
                for u in users:
                    send_message(u, "📈 Gold is rising!")
                last_alert = "up"

        except Exception as e:
            print("Error:", e)

        time.sleep(300)

if __name__ == "__main__":
    import threading
    threading.Thread(target=check_price).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
