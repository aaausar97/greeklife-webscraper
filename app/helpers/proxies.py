import json
import os

with open('config.json', 'r') as f:
    config = json.load(f)

PROXY_USER = config['proxy']['username']
PROXY_PASS = config['proxy']['password']
PROXY = config['proxy']['endpoint']
PROXY_AUTH = f"https://{PROXY_USER}:{PROXY_PASS}@{PROXY}"
print(f'Using Proxy: {PROXY_AUTH}')

def switch_proxy():
    proxy = PROXY_AUTH
    os.environ['HTTPS_PROXY'] = proxy
    os.environ['HTTP_PROXY'] = proxy

def reset_proxy():
    os.environ['HTTPS_PROXY'] = ''
    os.environ['HTTP_PROXY'] = ''


class ProxyContext:
    def __enter__(self):
        switch_proxy()
    
    def __exit__(self, exc_type, exc_value, traceback):
        reset_proxy()