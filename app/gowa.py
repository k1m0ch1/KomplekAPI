import requests
from config import GOWA_BASE, GOWA_AUTH

def send_whatsapp_message(phone: str, message: str, reply_id: str = None, is_forwarded: bool = False):
    url = f"{GOWA_BASE}/send/message"
    payload = {
        "phone": f"{phone}@s.whatsapp.net",
        "message": message,
        "reply_message_id": reply_id,
        "is_forwarded": is_forwarded
    }
    resp = requests.post(url, json=payload, auth=GOWA_AUTH)
    return resp.status_code, resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else resp.text

