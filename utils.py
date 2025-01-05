import time
import uuid
import requests
from constants import (GREEN)

def send_request(session, available_taps, count, token, proxies, extra_headers=None):
    url = 'https://api-gw.geagle.online/tap'

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
        "timestamp": timestamp,
        "salt": salt
    }
    
    start_time = time.time()
    response = session.post(url, headers=base_headers, json=data, proxies=proxies, timeout=(5, 30))
    end_time = time.time()
    
    print(f"{GREEN}Запит тривав {end_time - start_time:.2f} секунд")
    return response.json()
