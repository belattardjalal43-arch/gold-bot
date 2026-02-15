import os
import requests
import time
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
users = set()
last_alert = None

def get_gold_price():
    url = f"https://api.metals.dev/v1/latest?api_key={API_KEY}&base=USD&symbols=XAU"
    r = requests.get(url).json()
    return float(r["metals"]["XAU"])

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
            price = get_gold_price()
            send_message(chat_id, f"💰 Gold price now: {price}$")

    return "ok"

def check_price():
    global last_alert
    while True:
        try:
            price = get_gold_price()

            if price <= 4600 and last_alert != "down":
                for u in users:
                    send_message(u, "📉 Gold dropped!")
                last_alert = "down"

            elif price >= 5600 and last_alert != "up":
                for u in users:
                    send_message(u, "📈 Gold is rising!")
                last_alert = "up"

        except:
            pass

        time.sleep(300)

if __name__ == "__main__":
    import threading
    threading.Thread(target=check_price).start()
    app.run(host="0.0.0.0", port=10000)
