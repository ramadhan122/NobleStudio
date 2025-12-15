import requests
from .messages import discount_wa_message

FONNTE_TOKEN = "U2x8AMwDnCicKEFES9x7"

def send_discount_whatsapp(booking, discount):
    if not booking.phone:
        return

    message = discount_wa_message(booking, discount)

    payload = {
        "target": booking.phone.replace("62", "").lstrip("0"),
        "message": message,
        "countryCode": "62"
    }

    headers = {
        "Authorization": FONNTE_TOKEN
    }

    response = requests.post(
        "https://api.fonnte.com/send",
        data=payload,
        headers=headers
    )

    print("FONNTE STATUS:", response.status_code)
    print("FONNTE RESPONSE:", response.text)
