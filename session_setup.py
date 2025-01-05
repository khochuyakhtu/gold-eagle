import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session(
    total_retries=5,
    backoff_factor=1,
    status_forcelist=None,
    allowed_methods=None
):
    if status_forcelist is None:
        status_forcelist = [500, 502, 503, 504]
    if allowed_methods is None:
        allowed_methods = ["GET", "POST"]
    
    session = requests.Session()
    
    retries = Retry(
        total=total_retries,           
        backoff_factor=backoff_factor, 
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods
    )
    
    adapter = HTTPAdapter(max_retries=retries)
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
