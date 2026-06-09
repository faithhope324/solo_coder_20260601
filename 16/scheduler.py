import time
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread, pyqtSignal
from wol_sender import WOLSender


class WakeScheduler(QThread):
    wake_triggered = pyqtSignal(str, str)
    schedule_completed = pyqtSignal(str)
    schedules_updated = pyqtSignal()

    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self._stop_flag = False
        self._triggered_dates = {}
        self._schedules_cache = None
        self._last_cache_refresh = None
        self._cache_refresh_interval = 30

    def stop(self):
        self._stop_flag = True

    def refresh_schedules_cache(self):
        now = datetime.now()
        if (self._schedules_cache is None or
                self._last_cache_refresh is None or
                (now - self._last_cache_refresh).total_seconds() > self._cache_refresh_interval):
            self._schedules_cache = self.device_manager.get_all_schedules()
            self._last_cache_refresh = now
        return self._schedules_cache

    def invalidate_cache(self):
        self._schedules_cache = None
        self._last_cache_refresh = None

    def check_schedules(self):
        now = datetime.now()
        schedules = self.refresh_schedules_cache()
        triggered = []
        current_date = now.date()

        for schedule in schedules:
            if not schedule.get('enabled', True):
                continue

            try:
                wake_time = datetime.strptime(schedule['wake_time'], '%H:%M')
                schedule_id = schedule['id']

                if (now.hour == wake_time.hour and
                        now.minute == wake_time.minute and
                        now.second < 5):

                    last_triggered = self._triggered_dates.get(schedule_id)
                    if last_triggered != current_date:
                        self._triggered_dates[schedule_id] = current_date
                        triggered.append(schedule)

            except Exception as e:
                print(f"Error parsing schedule time: {e}")

        return triggered

    def execute_wake(self, schedule):
        device = self.device_manager.get_device(schedule['device_id'])
        if device:
            success = WOLSender.send_magic_packet(device['mac'])
            if success:
                self.wake_triggered.emit(schedule['id'], device['name'])

            if schedule.get('repeat') == 'once':
                self.device_manager.update_schedule(schedule['id'], enabled=False)
                self.schedule_completed.emit(schedule['id'])
                self.invalidate_cache()

    def run(self):
        while not self._stop_flag:
            triggered_schedules = self.check_schedules()
            for schedule in triggered_schedules:
                self.execute_wake(schedule)

            time.sleep(1)
