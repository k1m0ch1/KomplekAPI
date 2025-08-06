from dotenv import load_dotenv
import os
import boto3

load_dotenv()

STEIN_AUTH = (os.getenv("STEIN_USERNAME"), os.getenv("STEIN_PASSWORD"))
STEIN_BASE = os.getenv("STEIN_BASE")
SHEET_PENGHUNI = os.getenv("STEIN_SHEET_PENGHUNI")
SHEET_MESSAGE = os.getenv("STEIN_SHEET_MESSAGE")

GOWA_BASE = os.getenv("GOWA_BASE")
GOWA_USERNAME = os.getenv("GOWA_USERNAME")
GOWA_PASSWORD = os.getenv("GOWA_PASSWORD")
GOWA_AUTH = (os.getenv("GOWA_USERNAME"), os.getenv("GOWA_PASSWORD")) 

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET").encode()

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto"
)
