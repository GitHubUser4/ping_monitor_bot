import os
import time
import requests

# === НАСТРОЙКИ ===
TARGET_IP = "ХХХ.ХХХ.ХХХ.ХХХ"  # IP упавшего сервера
TG_TOKEN = "ВАШ_ТОКЕН_БОТА"
CHAT_ID = "ВАШ_CHAT_ID"
INTERVAL = 600  # Интервал проверки в секундах (600 сек = 10 мин)
# =================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")

def check_ping():
    # Флаг -c 10 означает 10 пакетов (для Linux)
    # response == 0 означает, что хотя бы один пакет вернулся (сервер доступен)
    response = os.system(f"ping -c 10 {TARGET_IP} > /dev/null 2>&1")
    return response == 0

print(f"Запущен мониторинг {TARGET_IP}. Интервал: {INTERVAL} секунд.")
send_telegram(f"🤖 Мониторинг запущен. Ищу признаки жизни сервера {TARGET_IP}...")

while True:
    if check_ping():
        msg = f"🎉 Сервер {TARGET_IP} ОЖИЛ! Пинг успешно проходит."
        print(msg)
        send_telegram(msg)
        break  # Выходим из цикла, чтобы прекратить проверки
    
    print(f"[{time.strftime('%H:%M:%S')}] Сервер все еще лежит. Ждем...")
    time.sleep(INTERVAL)