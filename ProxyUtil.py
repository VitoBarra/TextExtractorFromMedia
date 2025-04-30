import requests

import requests
from requests.exceptions import RequestException

def test_proxy(ip, port, test_url="https://httpbin.org/ip", use_https=False):
    proxy = f"{ip}:{port}"
    if use_https:
        proxies = {"http": f"https://{proxy}"}
    else:
        proxies = {"http": f"http://{proxy}"}

    try:
        response = requests.get(test_url, proxies=proxies, timeout=5)
        if response.status_code == 200:
            print(f"Working proxy: {proxy}")
            return True
        else:
            print(f"Bad response from proxy: {response.status_code}")
    except RequestException as e:
        print(f"Proxy failed: {proxy} – {e}")

    return False






def fetch_proxies():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    response = requests.get(url)


    if response.status_code == 200:
        if response.text == "":
            print("No proxies found")
            return []
        proxy_list = response.text.strip().split('\n')
        proxy_obj = [{"ip": ip, "port": port} for ip, port in (proxy.split(':') for proxy in proxy_list)]

        for proxy in proxy_obj:
            print(f"IP: {proxy['ip']}, Port: {proxy['port']}")

        return proxy_obj
    else:
        print(f"Failed to fetch proxies. Status code: {response.status_code}")
        return []
