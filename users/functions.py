from .models import CustomUser
from rest_framework.response import Response
from rest_framework import status
from math import radians, sin, cos, sqrt, atan2
from django.core.mail import send_mail
from django.conf import settings
import requests

def haversine_distance(lat1, lon1, lat2, lon2):
    # Yer radiusi kilometrda
    R = 6371.0

    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance




def send_email_code(email, code):
    subject = "Tasdiqlash kodi"
    message = f"Sizning tasdiqlash kodingiz: {code}"
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    except Exception as e:
        print(f"Email yuborishda xatolik: {e}")

def send_telegram_code(message, chat_ids=None):
    if chat_ids is None:
        chat_ids = [settings.TELEGRAM_USER_ID1]
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Telegramga yuborishda xatolik: {e}")
