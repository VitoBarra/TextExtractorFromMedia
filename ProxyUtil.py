import requests
from requests.exceptions import RequestException
from swiftshadow.classes import ProxyInterface
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


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
    driver = webdriver.Chrome(options=options)
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
    return proxies



def fetch_proxy_swiftshadow():
    proxy_manager = ProxyInterface(
        countries=[],
        protocol="https",
        autoRotate=True,
    )

    while True:
        proxy = proxy_manager.get()
        if proxy is None:
            print("can't find proxy")
            return []
        return [{"ip":proxy.ip,"port":proxy.port}]


