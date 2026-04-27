import os
from pathlib import Path

from waitress import serve

from app import create_app
from runtime_config import load_runtime_config

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)


def main():
    app = create_app()
    config = load_runtime_config()
    host = str(config["bind_host"])
    port = int(config["port"])
    threads = int(config["threads"])
    serve(app, host=host, port=port, threads=threads)


if __name__ == "__main__":
    main()
