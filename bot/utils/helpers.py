from typing import Any
from requests import Session
from bot.config.constants import GREEN, RESET
import aiohttp
import requests
import re
import base64
import binascii

def check_proxy(http_client: aiohttp.ClientSession, proxies: dict[str, Any]) -> None:
        try:
            print(f"{RESET}1. {GREEN}Пробуємо підключитися через проксі: {proxies}")
            response = http_client.get(url='https://httpbin.org/ip', proxies=proxies, timeout=10)
            ip = (response.json()).get('origin')
            print(f"{GREEN}Проксі {ip} працює", "\n")
        except Exception as error:
            raise RuntimeError(f"{GREEN}Проксі не працює", "Error: {error}")

def get_secret(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        match = re.search(r'TAP_SECRET\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise ValueError('Змінна TAP_SECRET не знайдена.')

        tap_secret = match.group(1)
        print(f'Значення TAP_SECRET: {tap_secret}')

        try:
            secret_bytes = base64.b32decode(tap_secret, casefold=True)
            secret_hex = binascii.hexlify(secret_bytes).decode()
            print(f'Secret Hex: {secret_hex}')
            return secret_hex
        except Exception as e:
            raise ValueError(f'Помилка декодування TAP_SECRET: {e}')

    except requests.RequestException as e:
        raise SystemExit(f'Помилка завантаження файлу: {e}')
    except Exception as e:
        raise SystemExit(f'Помилка: {e}')