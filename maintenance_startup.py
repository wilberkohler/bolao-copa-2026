"""Run deployment maintenance tasks once, outside the web worker startup."""

import os

os.environ["BOLAO_RUN_STARTUP_MAINTENANCE"] = "1"

from app import create_app


create_app()
