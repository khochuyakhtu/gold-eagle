import time
import random
import logging
import http.client as http_client
import json
import requests

from constants import (
    MAGENTA, CYAN, YELLOW, GREEN, RED, BOLD, UNDERLINE, RESET,
    ascii_banner, tagline
)

from session_setup import create_session
from utils import send_request

print(f"{MAGENTA}{'=' * 70}{RESET}")
print(ascii_banner)
print(tagline)
print(f"{MAGENTA}{'=' * 70}{RESET}")

USER_AGENTS_FILE_PATH = 'user-configuration.json'

session = create_session(
    total_retries=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "POST"]
)

def main():
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
                print(f"{RESET}1. {GREEN}Пробуємо підключитися через проксі: {proxies}")
                check_response = session.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
                print(f"{GREEN}Проксі {check_response.text} працює", "\n")

                count = random.randint(150, 249)

                response_json = send_request(
                    session=session,
                    available_taps=available_taps,
                    count=count,
                    token=token,
                    proxies=proxies,
                    extra_headers=custom_headers
                )
                print(f"{RESET}2.{CYAN}Відповідь: {RESET} {response_json}")

                total_requests += 1

                delay = random.uniform(10, 30)
                print(f"{RESET}3.{YELLOW}Вираховуємо затримку:{RESET} {delay:.2f} секунд\n")
                time.sleep(delay)
                print(f"{RESET}4.{GREEN}Затримку в {delay:.2f} секунд завершено. Виконуємо наступний запит {RESET}\n")

                longDelayAfterRequest = 24
                if total_requests >= longDelayAfterRequest:
                    sleep_time = random.uniform(12 * 60, 17 * 60)
                    print(f"{RESET}5.{RED}Очікуємо {sleep_time:.2f} секунд після {longDelayAfterRequest} запитів...{RESET}\n")
                    time.sleep(sleep_time)
                    total_requests = 0
            except requests.exceptions.RequestException as e:
                print(f"{RED}Помилка під час звернення через {proxies}: {e}\n")
                print(f"{RED}Очікуємо 10 хвилин перед повторною спробою...\n")
                time.sleep(10 * 60)

if __name__ == "__main__":
    main()
