from django.conf import settings
import requests
def send_otp_to_telegram(phone, otp):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    message = f"Телефон номер: {phone}\nOTP код: {otp}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)