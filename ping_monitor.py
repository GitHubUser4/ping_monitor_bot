import os
import sys
import time
import argparse
import logging
import subprocess
import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def parse_args():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Production-ready Multi-Host Uptime Monitor with Telegram notifications."
    )
    # Принимаем строку хостов, дефолт берем из .env
    parser.add_argument('--hosts', type=str, default=os.getenv('TARGET_HOSTS'), 
                        help='Comma-separated target IPs or Domain names')
    parser.add_argument('--token', type=str, default=os.getenv('TG_TOKEN'), help='Telegram Token')
    parser.add_argument('--chat-id', type=str, default=os.getenv('CHAT_ID'), help='Telegram Chat ID')
    parser.add_argument('--interval', type=int, default=int(os.getenv('INTERVAL', 600)), help='Check interval (seconds)')
    parser.add_argument('--count', type=int, default=int(os.getenv('PING_COUNT', 10)), help='Ping packets count')
    
    args = parser.parse_args()
    
    errors = []
    if not args.hosts: errors.append("Target Hosts (--hosts or TARGET_HOSTS)")
    if not args.token: errors.append("Telegram Token (--token or TG_TOKEN)")
    if not args.chat_id: errors.append("Telegram Chat ID (--chat-id or CHAT_ID)")
    
    if errors:
        parser.error(f"Missing required parameters: {', '.join(errors)}")
        
    # Парсим строку хостов в чистый список без пробелов
    args.hosts_list = [h.strip() for h in args.hosts.split(',') if h.strip()]
    if not args.hosts_list:
        parser.error("Hosts list is empty or invalid.")
        
    return args

def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram notification: {e}")

def check_ping(host, count):
    try:
        # Пингуем хост (не важно, IP это или домен)
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "1", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Error executing ping command for {host}: {e}")
        return False

def main():
    args = parse_args()
    
    # Копируем список хостов, которые нужно отслеживать
    hosts_to_monitor = list(args.hosts_list)
    
    logging.info(f"Starting monitor for hosts: {', '.join(hosts_to_monitor)} (Interval: {args.interval}s)")
    
    hosts_str = ", ".join([f"`{h}`" for h in hosts_to_monitor])
    send_telegram(args.token, args.chat_id, f"🤖 *Мониторинг запущен.*\nОтслеживаю хосты: {hosts_str}")
    
    try:
        while hosts_to_monitor:
            still_down = []
            
            for host in hosts_to_monitor:
                if check_ping(host, args.count):
                    msg = f"🎉 *Хост {host} ОЖИЛ!*\nПинг успешно проходит."
                    logging.info(f"Success! Host {host} is up.")
                    send_telegram(args.token, args.chat_id, msg)
                    # Если ожил, не добавляем его в still_down (исключаем из мониторинга)
                else:
                    logging.info(f"Host {host} is still down.")
                    still_down.append(host)
            
            # Обновляем список серверов, которые всё еще лежат
            hosts_to_monitor = still_down
            
            if not hosts_to_monitor:
                logging.info("All target hosts are up. Exiting service.")
                send_telegram(args.token, args.chat_id, "🏁 *Все отслеживаемые серверы поднялись.* Мониторинг завершен.")
                break
                
            logging.info(f"Waiting {args.interval}s before next check...")
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        logging.info("Monitor stopped manually.")
    except Exception as e:
        logging.critical(f"Unhandled exception in main loop: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()