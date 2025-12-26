"""Скрипт для остановки других инстанций бота через удаление webhook."""
import sys
import requests

if len(sys.argv) < 2:
    print("❌ Использование: python stop_other_instances.py <BOT_TOKEN>")
    sys.exit(1)

TELEGRAM_BOT_TOKEN = sys.argv[1]

print("🔍 Проверяем текущий webhook...")
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
response = requests.get(url)
webhook_info = response.json()
print(f"Webhook URL: {webhook_info.get('result', {}).get('url', 'НЕ УСТАНОВЛЕН')}")

print("\n🗑️  Удаляем webhook (если установлен)...")
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
response = requests.get(url)
print(f"Результат: {response.json()}")

print("\n✅ Готово! Теперь бот на Railway должен работать без конфликтов.")
print("   Подождите 10-20 секунд и проверьте логи в Railway.")
