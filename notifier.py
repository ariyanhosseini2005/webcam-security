import os
import json
import requests

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG.get('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = CONFIG.get('TELEGRAM_CHAT_ID', '')

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = f"{API_BASE}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}
        r = requests.post(url, data=payload, timeout=10)
        return r.ok
    except Exception:
        return False

def send_photo(photo_path: str, caption: str = "") -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        return False
    if not os.path.isfile(photo_path):
        return False
    try:
        url = f"{API_BASE}/sendPhoto"
        with open(photo_path, 'rb') as img:
            files = {"photo": img}
            data = {"chat_id": CHAT_ID, "caption": caption}
            r = requests.post(url, files=files, data=data, timeout=20)
        return r.ok
    except Exception:
        return False
