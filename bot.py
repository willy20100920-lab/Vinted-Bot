import os, time, json, requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID        = os.environ.get("CHAT_ID", "")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))

SEARCHES = [
    {"keyword": "jordan 1 travis scott", "max_price": 300},
    {"keyword": "nike dunk low",          "max_price": 150},
]

SEEN_IDS_FILE = "seen_ids.json"

def load_seen_ids():
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen_ids(ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(ids), f)

def fetch_vinted(keyword, max_price):
    url = "https://www.vinted.it/api/v2/catalog/items"
    params = {"search_text": keyword, "order": "newest_first",
              "per_page": 20, "price_to": max_price}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}
    session = requests.Session()
    session.get("https://www.vinted.it", headers=headers, timeout=10)
    r = session.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def send_telegram(item, keyword):
    price    = item.get("price", {})
    price_s  = f"{price.get('amount','?')} {price.get('currency_code','EUR')}"
    url      = f"https://www.vinted.it/items/{item.get('id')}"
    photo    = item.get("photo", {}).get("url", "")
    text = (f"🔔 *Nuovo annuncio!*\n🔍 `{keyword}`\n\n"
            f"👟 *{item.get('title','')}*\n"
            f"💶 {price_s}  🏷️ {item.get('brand_title','')}  "
            f"📐 {item.get('size_title','')}\n\n🔗 [Vedi su Vinted]({url})")
    ep = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    if photo:
        requests.post(f"{ep}/sendPhoto",
            json={"chat_id": CHAT_ID,"photo": photo,"caption": text,"parse_mode":"Markdown"}, timeout=10)
    else:
        requests.post(f"{ep}/sendMessage",
            json={"chat_id": CHAT_ID,"text": text,"parse_mode":"Markdown"}, timeout=10)

def main():
    print(f"Bot avviato — controllo ogni {CHECK_INTERVAL}s")
    seen = load_seen_ids()
    while True:
        for s in SEARCHES:
            try:
                items = fetch_vinted(s["keyword"], s["max_price"])
                for item in items:
                    iid = str(item.get("id"))
                    if iid not in seen:
                        seen.add(iid)
                        send_telegram(item, s["keyword"])
                        time.sleep(1)
                save_seen_ids(seen)
                print(f"[{datetime.now():%H:%M:%S}] {s['keyword']}: OK")
            except Exception as e:
                print(f"ERRORE {s['keyword']}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
