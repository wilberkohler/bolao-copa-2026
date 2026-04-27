import os
import socket
import threading
from pathlib import Path

import servicemanager
import win32event
import win32service
import win32serviceutil
from waitress.server import create_server

from app import create_app
from runtime_config import load_runtime_config

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)


class BolaoWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BolaoCopa2026"
    _svc_display_name_ = "Bolao Copa 2026"
    _svc_description_ = "Servidor web do sistema de bolao da Copa 2026."

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.server = None
        self.server_thread = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.server is not None:
            self.server.close()
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("Bolao Copa 2026 service starting")
        self.main()
        servicemanager.LogInfoMsg("Bolao Copa 2026 service stopped")

    def main(self):
        app = create_app()
        config = load_runtime_config()
        host = str(config["bind_host"])
        port = int(config["port"])
        threads = int(config["threads"])

        self.server = create_server(app, host=host, port=port, threads=threads)
        self.server_thread = threading.Thread(target=self.server.run, name="bolao-waitress", daemon=True)
        self.server_thread.start()

        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        if self.server_thread.is_alive():
            self.server_thread.join(timeout=10)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(BolaoWindowsService)
