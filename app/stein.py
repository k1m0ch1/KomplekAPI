import requests
from config import STEIN_BASE, STEIN_AUTH, SHEET_PENGHUNI, SHEET_MESSAGE

def get_penghuni_with_tagihan():
    url = f"{STEIN_BASE}/penghuni"
    resp = requests.get(url, auth=STEIN_AUTH)
    resp.raise_for_status()
    data = resp.json()
    return [r for r in data if r.get("tagihan_ipl") and int(r["tagihan_ipl"]) > 0]

def get_message_template():
    url = f"{STEIN_BASE}/message?search={{\"keperuntukan\":\"pemberitahuan lengkap\"}}"
    resp = requests.get(url, auth=STEIN_AUTH)
    resp.raise_for_status()
    data = resp.json()
    return data[0].get("pesan") if data else ""

