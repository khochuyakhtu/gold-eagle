import time
import random
import json
import requests
import uuid
from datetime import datetime
import base64
import random
import base64
import hmac
import hashlib
import time
import struct

from bot.config.constants import (
    MAGENTA, CYAN, YELLOW, GREEN, RED, BOLD, UNDERLINE, RESET,
    ascii_banner, tagline
)

from session_setup import create_session

BYTES_HEX = "3132333435363738393031323334353637383930" #This code can be updated. TODO: Get code per each request
ACCOUNTS_COUNT = 7

totp_options = {
    "encoding": "HEX",
    "digits": 6,
    "step": 2,
    "algorithm": "SHA1",
}

def create_digest(key, counter, algorithm):
    hmac_digest = hmac.new(
        key=key,
        msg=counter.to_bytes(8, byteorder="big"),
        digestmod=getattr(hashlib, algorithm.lower())
    ).digest()
    return hmac_digest

def showDelay(step, sleep_time):
    print(f"{RESET}{step}.{RED}Затримка: {sleep_time:.2f} секунд")
    for remaining in range(int(sleep_time), 0, -1):
        minutes = remaining // 60
        seconds = remaining % 60
                        
        print(f"\r{RESET}{RED}Очікуємо {minutes:02d}:{seconds:02d} до завершення затримки.", end="")
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

def hotp(key, counter, digits=6, digest='sha1'):
    key = base64.b32decode(key.upper() + '=' * ((8 - len(key)) % 8))
    counter = struct.pack('>Q', counter)
    mac = hmac.new(key, counter, digest).digest()
    offset = mac[-1] & 0x0f
    binary = struct.unpack('>L', mac[offset:offset+4])[0] & 0x7fffffff
    otp_str = str(binary)[-digits:].zfill(digits)

    return base64.b64encode(otp_str.encode()).decode()

def send_request(session, available_taps, count, token, proxies, extra_headers=None):
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
    
    generated_nonce = generate_totp_in_base64(secret_hex=BYTES_HEX)

    data = {
        "available_taps": available_taps,
        "count": count,
        "nonce": generated_nonce,
        "salt": salt,
        "timestamp": timestamp
    }
    
    start_time = time.time()


    response = session.post(url, headers=base_headers, json=data, proxies=proxies, timeout=(10, 30))
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

            print(f"\n{GREEN}==================================================")
            print(f"{GREEN}{BOLD}Виконуємо запит для акаунту: {account_name}")
            print(f"{GREEN}==================================================\n")
            if proxy_url.strip().lower() == "no proxy":
                proxies = {}
            else:
                proxies = {"http": proxy_url, "https": proxy_url}

            try:
                print(f"{RESET}1. {GREEN}Пробуємо підключитися через проксі")
                session.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
                print(f"{GREEN}Проксі працює")

                count = random.randint(800, 900)

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

                if total_requests >= ACCOUNTS_COUNT:
                    current_hour = datetime.now().hour
                    if 0 <= current_hour < 7:
                        sleep_time = random.uniform(30 * 60, 60 * 60)
                    else:
                        sleep_time = random.uniform(11 * 60, 14 * 60)

                    showDelay(5, sleep_time)

                    total_requests = 0
            except requests.exceptions.RequestException as e:
                print(f"{RED}Помилка під час звернення через {proxies}: {e}\n")
                print(f"{RED}Очікуємо 10 хвилин перед повторною спробою...\n")
                time.sleep(10 * 60)