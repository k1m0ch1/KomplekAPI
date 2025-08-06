from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import json
import re
import boto3
import requests
from io import BytesIO
import config as cfg 

app = FastAPI()

WEBHOOK_SECRET = cfg.WEBHOOK_SECRET
S3_BUCKET_URL = cfg.R2_ENDPOINT
S3_BUCKET_NAME = cfg.R2_BUCKET_NAME
GOWA_API = cfg.GOWA_BASE 
GOWA_USERNAME = cfg.GOWA_USERNAME 
GOWA_PASSWORD = cfg.GOWA_PASSWORD

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
    match = re.match(r"IPL\s+(\w+)\s+bulan\s+([A-Za-z]+)\s+tahun\s+(\d{4})", text, re.IGNORECASE)
    if match:
        return match.groups()  # (blok, bulan, tahun)
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
        "receiver": to,
        "message": message
    }
    response = requests.post(
        f"{GOWA_API}/send-message",
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
    print(payload["image"])

    image = payload["image"]
    image_caption = image["caption"] if image else None
    sender = payload["sender"] 
    #file_url = payload.get("file_url")  # ← GOWA webhook includes this for media
    file_url = image["media_path"] if image else None

    parsed = parse_iplnotif(image_caption)
    if parsed and file_url:
        blok, bulan, tahun = parsed

        # Download the media (e.g., image)
        # media_resp = requests.get(file_url, auth=(GOWA_USERNAME, GOWA_PASSWORD))

        try:
            with open(file_url, "rb") as f:
            file_bytes = f.read()
        except FileNotFoundError:
            print(f"⚠ File not found: {file_url}")
            return {"status": "file not found"}

        filename = f"{blok}-{bulan}-{tahun}.jpg"
        key = f"{tahun}/{bulan}/{filename}"
        upload_to_r2(file_bytes, key)

        # Reply to sender
        reply_message(sender, "Terima kasih, sudah membayar, bukti pembayaran akan kami cek dan akan di konfirmasi")
        return {"status": "uploaded and replied"}

    return {"status": "received"}

