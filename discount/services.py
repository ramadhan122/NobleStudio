import requests
from .messages import discount_wa_message
from django.conf import settings

def send_discount_whatsapp(booking, discount):
    if not booking.phone:
        return

    message = discount_wa_message(booking, discount)

    phone = booking.phone

    # normalisasi nomor Indonesia
    if phone.startswith("0"):
        phone = "62" + phone[1:]

    payload = {
        "target": phone,
        "message": message
    }

    headers = {
        "Authorization": settings.FONNTE_TOKEN
    }

    response = requests.post(
        "https://api.fonnte.com/send",
        data=payload,
        headers=headers
    )

    print("FONNTE STATUS:", response.status_code)
    print("FONNTE RESPONSE:", response.text)

    return response.text