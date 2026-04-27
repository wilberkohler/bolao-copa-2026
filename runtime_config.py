import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "service_config.json"

DEFAULT_CONFIG = {
    "bind_host": "127.0.0.1",
    "public_host": "127.0.0.1",
    "port": 5000,
    "threads": 8,
    "debug": True,
}


def load_runtime_config():
    config = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
        config.update({key: value for key, value in loaded.items() if value is not None})
    return config
