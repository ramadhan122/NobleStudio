import requests
from django.conf import settings

def send_wa_fonnte(phone, message):
    url = "https://api.fonnte.com/send"
    headers = {
        "Authorization": settings.FONNTE_TOKEN
    }
    payload = {
        "target": phone,
        "message": message
    }

    response = requests.post(url, headers=headers, data=payload)
    return response.json()
