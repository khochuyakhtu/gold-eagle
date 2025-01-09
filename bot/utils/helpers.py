from typing import Any
from requests import Session
from bot.config.constants import GREEN, RESET
import aiohttp

def check_proxy(http_client: aiohttp.ClientSession, proxies: dict[str, Any]) -> None:
        try:
            print(f"{RESET}1. {GREEN}Пробуємо підключитися через проксі: {proxies}")
            response = http_client.get(url='https://httpbin.org/ip', proxies=proxies, timeout=10)
            ip = (response.json()).get('origin')
            print(f"{GREEN}Проксі {ip} працює", "\n")
            #logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            raise RuntimeError(f"{GREEN}Проксі не працює", "Error: {error}")
            #logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")