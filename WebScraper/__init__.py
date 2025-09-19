from pathlib import Path

BASE_DIR = Path(__file__).parent

PROXY_DIR = BASE_DIR / "proxies"
PROXY_FILE = PROXY_DIR/'proxy_list.json'

PROXY_DIR.mkdir(parents=True, exist_ok=True)