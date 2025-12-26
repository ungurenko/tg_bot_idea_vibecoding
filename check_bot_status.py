"""Проверка статуса Telegram бота."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не установлен!")
    print("Введите токен вручную:")
    TELEGRAM_BOT_TOKEN = input("Token: ").strip()

# Проверяем информацию о боте
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
response = requests.get(url)
print("\n📱 Информация о боте:")
print(response.json())

# Проверяем webhook
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
response = requests.get(url)
webhook_info = response.json()
print("\n🔗 Webhook информация:")
print(f"URL: {webhook_info.get('result', {}).get('url', 'НЕ УСТАНОВЛЕН (polling mode)')}")
print(f"Pending updates: {webhook_info.get('result', {}).get('pending_update_count', 0)}")
print(f"Last error: {webhook_info.get('result', {}).get('last_error_message', 'Нет ошибок')}")

# Проверяем последние обновления
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=1"
response = requests.get(url)
updates = response.json()
print(f"\n📨 Последние обновления: {len(updates.get('result', []))} сообщений в очереди")
