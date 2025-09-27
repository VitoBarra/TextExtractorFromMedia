import ipaddress

import requests
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from swiftshadow.classes import ProxyInterface

from Utility.FileUtil import ReadJson, WriteJson, IsModifiedRecently
from WebScraper import PROXY_FILE


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



# Filtro degli IP validi
def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def fetch_proxies():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    response = requests.get(url)


    if response.status_code == 200:
        if response.text == "":
            print("No proxies found")
            return []
        proxy_list = response.text.strip().split('\r\n')
        proxy_obj = [{"ip": ip, "port": port} for ip, port in (proxy.split(':') for proxy in proxy_list)]
        proxy_obj = [proxy for proxy in proxy_obj if is_valid_ip(proxy["ip"])]

        return proxy_obj
    else:
        print(f"Failed to fetch proxies. Status code: {response.status_code}")
        return []





# Lista globale per salvare i proxy
def fetchHTTPS_proxies():
    proxies = []
    proxies.clear()  # Svuoto la lista

    # Opzioni per esecuzione headless
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    print("Fetching HTTPS proxies")
    # Inizializzo il driver
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.sslproxies.org/')

    # Trova tutte le righe della tabella
    rows = driver.find_elements(By.CSS_SELECTOR, 'table.table tbody tr')
    print(f"founded {len(rows)} proxies")

    for row in rows:
        columns = row.find_elements(By.TAG_NAME, 'td')
        if len(columns) >= 2:
            proxies.append({
                'ip': columns[0].text,
                'port': columns[1].text
            })

    driver.quit()
    filtered_proxies = [proxy for proxy in proxies if is_valid_ip(proxy["ip"])]
    return filtered_proxies



def fetch_proxy_swiftshadow(find_https = True):
    proxy_manager = ProxyInterface(
        countries=[],
        protocol= "https" if find_https else "http",
        autoRotate=True,
    )

    proxy_list = []
    for i in range(100):
        proxy = proxy_manager.get()
        if proxy is None:
            print("can't find proxy")
            continue
        proxy_list.append({"ip":proxy.ip,"port":proxy.port})
    return proxy_list


def getProxyList(proxy_file=PROXY_FILE, MAX_AGE_SECONDS = 1800):
     # Check if file is recent and use it, otherwise call the function
    if IsModifiedRecently(proxy_file, MAX_AGE_SECONDS):
        proxy_list = ReadJson(proxy_file)
        print(f"Loaded {len(proxy_list)} proxies from file {proxy_file}")
        if len(proxy_list) != 0:
            return proxy_list

    print("...finding new proxy")
    proxy_list = fetch_proxies()
    WriteJson(proxy_file, proxy_list)
    print(f"Downloaded {len(proxy_list)} proxies and saved to file {proxy_file}")

    return proxy_list
