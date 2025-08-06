from fastapi import FastAPI
from app.stein import get_penghuni_with_tagihan, get_message_template
from app.gowa import send_whatsapp_message

app = FastAPI()

@app.get("/send-messages")
def send_messages():
    penghuni = get_penghuni_with_tagihan()
    template = get_message_template()

    print(penghuni)
    results = []

    for r in penghuni:
        phone = r.get("No Tlp")
        name = r.get("Nama", "")
        rumah = r.get("Nomor Rumah", "")
        message = template.replace("{nama}", name).replace("{nomor_rumah}", rumah)

        status, resp = send_whatsapp_message(phone, message)
        results.append({"to": f"{phone}@s.whatsapp.net", "status": status, "response": resp})

    return {"sent_count": len(results), "details": results}

