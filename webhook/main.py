from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import json
import re
import boto3
import requests
from io import BytesIO
import config as cfg 
from datetime import datetime

app = FastAPI()

WEBHOOK_SECRET = cfg.WEBHOOK_SECRET
S3_BUCKET_URL = cfg.R2_ENDPOINT
S3_BUCKET_NAME = cfg.R2_BUCKET_NAME
GOWA_API = cfg.GOWA_BASE 
GOWA_USERNAME = cfg.GOWA_USERNAME 
GOWA_PASSWORD = cfg.GOWA_PASSWORD
R2_PUBLIC = cfg.R2_PUBLIC

# Configure boto3 for R2
s3 = boto3.client(
    "s3",
    endpoint_url=S3_BUCKET_URL,
    aws_access_key_id=cfg.R2_ACCESS_KEY,
    aws_secret_access_key=cfg.R2_SECRET_KEY,
    region_name="auto",
)

def verify_signature(body: bytes, signature: str) -> bool:
    if signature is None:
        raise HTTPException(status_code=400, detail="Missing signature header: X-Hub-Signature")

    mac = hmac.new(WEBHOOK_SECRET, msg=body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature)

def parse_iplnotif(text: str):
    try:
        parts = text.lower().strip().split()
        if parts[0] != "ipl":
            return None

        blok = parts[1]
        bulan_index = parts.index("bulan")
        tahun_index = parts.index("tahun")

        bulan = parts[bulan_index + 1]
        tahun = parts[tahun_index + 1]

        return blok.upper(), bulan.capitalize(), tahun
    except (ValueError, IndexError):
        return None


def upload_to_r2(file_bytes: bytes, key: str):
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType="image/jpeg"
    )

def reply_message(to: str, message: str):
    payload = {
        "phone": to,
        "message": message
    }
    response = requests.post(
        f"{GOWA_API}/send/message",
        auth=(GOWA_USERNAME, GOWA_PASSWORD),
        json=payload
    )
    return response.ok

@app.post("/webhook")
async def webhook_handler(
    request: Request,
    x_hub_signature: str = Header(default=None)
):
    body = await request.body()

    # if x_hub_signature is None:
    #    raise HTTPException(status_code=400, detail="Missing X-Hub-Signature header")

    # if not verify_signature(body, x_hub_signature):
    #    raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)
    event = payload.get("event")   

    print(payload)

    if "image" in payload:

        image = payload["image"]
        image_caption = image["caption"] if image else None
        sender = payload["sender_id"] 
        #file_url = payload.get("file_url")  # ← GOWA webhook includes this for media
        file_url = image["media_path"] if image else None

        parsed = parse_iplnotif(image_caption)
        if parsed and file_url:
            blok, bulan, tahun = parsed
    
            # Download the media (e.g., image)
            media_resp = requests.get(f"{GOWA_API}/{file_url}")
            if media_resp.status_code == 200:
                filename = f"{blok}-{bulan}-{tahun}.jpg"
                key = f"{tahun}/{bulan}/{filename}"
                upload_to_r2(media_resp.content, key)
                public_url = f"{cfg.R2_PUBLIC}/{key}"

                row = {
                    "transfered_at": datetime.now().strftime("%Y-%m-%d"),
                    "Nomor Rumah": blok,
                    "Bukti Bayar": public_url,
                    "dibayarkan oleh": sender,
                }

                stein_response = requests.post(f"{cfg.STEIN_BASE}/tagihan", json=[row], auth=cfg.STEIN_AUTH)
                print("📄 Stein insert status:", stein_response.status_code, stein_response.text)
    
                # Reply to sender
                reply_message(sender, "Terima kasih, sudah membayar, bukti pembayaran akan kami cek dan akan di konfirmasi")
        return {"status": "uploaded and replied"}

    return {"status": "received"}

