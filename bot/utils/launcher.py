import time
import random
import json
import requests
import uuid
from datetime import datetime

from bot.config.constants import (
    MAGENTA, CYAN, YELLOW, GREEN, RED, BOLD, UNDERLINE, RESET,
    ascii_banner, tagline
)

from session_setup import create_session

def showDelay(step, sleep_time):
    print(f"{RESET}{step}.{RED}Затримка: {sleep_time:.2f} секунд")
    for remaining in range(int(sleep_time), 0, -1):
        minutes = remaining // 60
        seconds = remaining % 60
                        
        print(f"\r{RESET}5.{RED}Очікуємо {minutes:02d}:{seconds:02d} до завершення затримки.\n", end="")
        time.sleep(1)

def send_request(session, available_taps, count, token, proxies, extra_headers=None):
    # url = 'https://api-gw.geagle.online/tap'
    url = 'https://gold-eagle-api.fly.dev/tap'
    base_headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'uk',
        'authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'origin': 'https://telegram.geagle.online',
        'priority': 'u=1, i',
        'referer': 'https://telegram.geagle.online/',
        'sec-ch-ua': '"Google Chrome";v="103", "Chromium";v="103", "Not_A Brand";v="8"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.3)'
    }

    if extra_headers:
        base_headers.update(extra_headers)

    timestamp = int(time.time())
    salt = str(uuid.uuid4())
    
    data = {
        "available_taps": available_taps,
        "count": count,
        "salt": salt,
        "timestamp": timestamp
    }
    
    start_time = time.time()
    response = session.post(url, headers=base_headers, json=data, proxies=proxies, timeout=(5, 30))
    end_time = time.time()
    
    print(f"{GREEN}Запит тривав {end_time - start_time:.2f} секунд")
    return response.json()

async def process():
    print(f"{MAGENTA}{'=' * 70}{RESET}")
    print(ascii_banner)
    print(tagline)
    print(f"{MAGENTA}{'=' * 70}{RESET}")

    USER_AGENTS_FILE_PATH = './bot/config/user-configuration.json'

    session = create_session(
        total_retries=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )

    with open(USER_AGENTS_FILE_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    available_taps = 1000
    total_requests = 0

    while True:
        for account_cfg in config_data:
            token = account_cfg["token"]
            proxy_url = account_cfg["proxy"]
            custom_headers = account_cfg["headers"]
            account_name = account_cfg["name"]

            print(f"{GREEN}==================================================")
            print(f"{GREEN}{BOLD}Виконуємо запит для акаунту: {account_name}")
            print(f"{GREEN}==================================================\n")
            if proxy_url.strip().lower() == "no proxy":
                proxies = {}
            else:
                proxies = {"http": proxy_url, "https": proxy_url}

            try:
                print(f"{RESET}1. {GREEN}Пробуємо підключитися через проксі")
                check_response = session.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
                print(f"{GREEN}Проксі працює")

                count = random.randint(140, 289)

                response_json = send_request(
                    session=session,
                    available_taps=available_taps,
                    count=count,
                    token=token,
                    proxies=proxies,
                    extra_headers=custom_headers
                )
                print(f"{RESET}2.{CYAN}Відповідь: {RESET} {response_json}. Нараховано: {count} коіни")

                total_requests += 1

                delay = random.uniform(10, 30)
                
                print(f"{RESET}3.{YELLOW}Вираховуємо затримку:{RESET} {delay:.2f} секунд\n")
                showDelay(4, delay)

                longDelayAfterRequest = 56
                if total_requests >= longDelayAfterRequest:
                    current_hour = datetime.now().hour
                    if 0 <= current_hour < 7:
                        sleep_time = random.uniform(50 * 60, 80 * 60)
                    else:
                        sleep_time = random.uniform(11 * 60, 18 * 60)

                    showDelay(5, sleep_time)

                    total_requests = 0
            except requests.exceptions.RequestException as e:
                print(f"{RED}Помилка під час звернення через {proxies}: {e}\n")
                print(f"{RED}Очікуємо 10 хвилин перед повторною спробою...\n")
                time.sleep(10 * 60)