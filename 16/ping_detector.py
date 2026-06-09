import subprocess
import platform
import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal


class PingDetector(QThread):
    status_updated = pyqtSignal(str, str)
    detection_complete = pyqtSignal()

    def __init__(self, device_manager, interval=60):
        super().__init__()
        self.device_manager = device_manager
        self.interval = interval
        self._stop_flag = False
        self._devices_cache = None
        self._last_cache_refresh = None
        self._cache_refresh_interval = 30

    def stop(self):
        self._stop_flag = True

    def invalidate_cache(self):
        self._devices_cache = None
        self._last_cache_refresh = None

    def refresh_devices_cache(self):
        now = datetime.now()
        if (self._devices_cache is None or
                self._last_cache_refresh is None or
                (now - self._last_cache_refresh).total_seconds() > self._cache_refresh_interval):
            self._devices_cache = self.device_manager.get_all_devices()
            self._last_cache_refresh = now
        return self._devices_cache

    @staticmethod
    def ping(ip, timeout=1):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        wait_param = '-w' if platform.system().lower() == 'windows' else '-W'
        timeout_ms = str(timeout * 1000 if platform.system().lower() == 'windows' else timeout)
        command = ['ping', param, '1', wait_param, timeout_ms, ip]
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 1
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_device(self, device):
        try:
            is_online = self.ping(device['ip'], timeout=1)
            status = 'online' if is_online else 'offline'
            self.status_updated.emit(device['id'], status)
            self.device_manager.update_device_status(device['id'], status)
            return status
        except Exception as e:
            print(f"Error checking device {device['name']}: {e}")
            self.status_updated.emit(device['id'], 'unknown')
            return 'unknown'

    def check_all_devices(self):
        devices = self.refresh_devices_cache()
        for device in devices:
            if self._stop_flag:
                break
            if device.get('ip'):
                self.check_device(device)
        self.detection_complete.emit()

    def run(self):
        while not self._stop_flag:
            self.check_all_devices()
            for _ in range(self.interval):
                if self._stop_flag:
                    break
                time.sleep(1)
