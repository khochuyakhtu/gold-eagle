import time
import random
import json
import requests
import uuid
import base64
import hmac
import hashlib

from datetime import datetime
from bot.config.constants import (CYAN, YELLOW, GREEN, RED, BOLD, RESET)
from bot.utils.helpers import get_secret, get_sleep_time
from session_setup import create_session

TAP_API_URL = 'https://gold-eagle-api.fly.dev/tap'
ME_API_URL = 'https://gold-eagle-api.fly.dev/user/me/progress'
MAX_RETRIES = 3
USER_AGENTS_FILE_PATH = './bot/config/user-configuration.json'
SECRET_URL = 'https://telegram.geagle.online/assets/index-DI7KSCOy.js'
DAY_DELAY_IN_MINUTES = (10, 14) # затримка протягом дня від 10 до 14 хвилин
NIGHT_DELAY_IN_MINUTES = (20, 50) # затримка протягом ночі від 20 до 50 хвилин
NIGHT_HOURS = (0, 7) # Діапазон годин для нічного часу (0:00 - 6:59)
PERSENTAGE_FROM_AVAILABLE_ENERGY = (0.1, 0.99) # % від доступної енергії (10%-99%)

def showDelay(step, sleep_time):
    print(f"\r{RESET}{step}.{YELLOW} Затримка: {RESET}{sleep_time:.2f} секунд(и)")
    for remaining in range(int(sleep_time), 0, -1):
        minutes = remaining // 60
        seconds = remaining % 60
                        
        print(f"\r{step+1}. {CYAN}Очікуємо: {RESET}{minutes:02d}:{seconds:02d} до завершення затримки.", end="")
        time.sleep(1)

def generate_totp_in_base64(secret_hex, step=2, digits=6, algorithm=hashlib.sha1):
    secret_bytes = bytes.fromhex(secret_hex)
    time_counter = int(time.time() // step)
    time_counter_bytes = time_counter.to_bytes(8, byteorder="big")
    hmac_hash = hmac.new(secret_bytes, time_counter_bytes, algorithm).digest()
    offset = hmac_hash[-1] & 0x0F
    code_int = int.from_bytes(hmac_hash[offset:offset+4], byteorder="big") & 0x7FFFFFFF
    otp = code_int % (10 ** digits)
    otp_str = str(otp).zfill(digits)
    otp_base64 = base64.b64encode(otp_str.encode()).decode()
    
    return otp_base64

def create_headers(token, extra_headers=None):
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
    return base_headers

def fetch_secret():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return get_secret(SECRET_URL)
        except SystemExit as e:
            print(f'Спроба {attempt} не вдалася: {e}')
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                print('Усі спроби вичерпано. Завершення програми.')
                exit(1)
        except Exception as ex:
            print(f"{RED}Помилка під час отримання секрету: {ex}{RESET}")
            exit(1)

def prepare_data(available_taps, count, secret):
    generated_nonce = generate_totp_in_base64(secret_hex=secret)
    data = {
        "available_taps": available_taps,
        "count": count,
        "nonce": generated_nonce,
        "salt": str(uuid.uuid4()),
        "timestamp": int(time.time())
    }
    return data

def send_tap_request(session, data, headers, proxies):
    start_time = time.time()
    response = session.post(TAP_API_URL, headers=headers, json=data, proxies=proxies, timeout=(10, 30))
    end_time = time.time()
    print(f"{RESET}8. {CYAN}Запит до {GREEN}{TAP_API_URL}{CYAN} тривав {end_time - start_time:.2f} секунд")
    return response.json()

def send_me_request(session, headers, proxies):
    start_time = time.time()
    response = session.get(ME_API_URL, headers=headers, proxies=proxies, timeout=(10, 30))
    end_time = time.time()
    print(f"{RESET}3. {YELLOW}Запит до {GREEN}{ME_API_URL}{YELLOW} тривав {end_time - start_time:.2f} секунд")
    return response.json()

def send_request(session, available_taps, count, token, proxies, headers):
    secret = fetch_secret()
    data = prepare_data(available_taps, count, secret)
    return send_tap_request(session, data, headers, proxies)

async def process():
    session = create_session(
        total_retries=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )

    with open(USER_AGENTS_FILE_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    total_requests = 0

    while True:
        for account_cfg in config_data:
            token = account_cfg["token"]
            proxy_url = account_cfg["proxy"]
            custom_headers = account_cfg["headers"]
            account_name = account_cfg["name"]
            max_available_taps = account_cfg["max_available_taps"]
            coins_per_click = account_cfg["coins_per_click"]

            print(f"\n{GREEN}==================================================")
            print(f"{GREEN}{BOLD}Виконуємо запит для акаунту: {account_name}")
            print(f"{GREEN}==================================================\n")
            if proxy_url.strip().lower() == "no proxy":
                proxies = {}
            else:
                proxies = {"http": proxy_url, "https": proxy_url}

            try:
                print(f"{RESET}1. {YELLOW}Пробуємо підключитися через проксі")
                session.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
                print(f"{RESET}2. {CYAN}Проксі працює")

                headers = create_headers(token, custom_headers)

                user_information_json = send_me_request(session=session, headers=headers, proxies=proxies)
                coins_amount = user_information_json["coins_amount"]
                energy = user_information_json["energy"]
                print(f"{RESET}4. {CYAN}Доступна енергія: {energy}")
                print(f"{RESET}5. {YELLOW}Поточна кількість монет:{coins_amount}")

                taps_count = int(energy * random.uniform(PERSENTAGE_FROM_AVAILABLE_ENERGY[0], PERSENTAGE_FROM_AVAILABLE_ENERGY[1])/ coins_per_click) 

                response_json = send_request(
                    session=session,
                    available_taps=max_available_taps,
                    count=taps_count,
                    token=token,
                    proxies=proxies,
                    headers=headers
                )
                print(f"{RESET}9. {YELLOW}Відповідь сервера: {RESET} {response_json}. {YELLOW}Нараховано: {RESET}{taps_count} коіни")

                total_requests += 1

                delay = random.uniform(5, 20)
                
                print(f"{RESET}10. {CYAN}Вираховуємо затримку:{RESET} {delay:.2f} секунд(и)")
                showDelay(11, delay)

                if total_requests >= len(config_data):
                    sleep_time = get_sleep_time(DAY_DELAY_IN_MINUTES, NIGHT_DELAY_IN_MINUTES, NIGHT_HOURS)
                    showDelay(12, sleep_time)

                    total_requests = 0
            except requests.exceptions.RequestException as e:
                print(f"{RED}Помилка під час звернення через {proxies}: {e}\n")
                print(f"{RED}Очікуємо 10 хвилин перед повторною спробою...\n")
                time.sleep(10 * 60)
