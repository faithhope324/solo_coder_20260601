import time
from datetime import datetime, date
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from wol_sender import WOLSender


class WakeScheduler(QThread):
    wake_triggered = pyqtSignal(str, str)
    schedule_completed = pyqtSignal(str)

    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self._stop_flag = False
        self._mutex = QMutex()
        self._schedules_cache = []
        self._last_check_minute = -1
        self._current_date = date.today()
        self._triggered_schedules = set()
        self._cache_dirty = True

    def stop(self):
        self._stop_flag = True

    def refresh_schedules(self):
        with QMutexLocker(self._mutex):
            self._cache_dirty = True

    def _load_schedules(self):
        with QMutexLocker(self._mutex):
            if self._cache_dirty:
                self._schedules_cache = self.device_manager.get_all_schedules()
                self._cache_dirty = False
            return list(self._schedules_cache)

    def _check_date_change(self):
        today = date.today()
        if today != self._current_date:
            self._current_date = today
            self._triggered_schedules.clear()
            self._last_check_minute = -1

    def _get_schedules_for_now(self, now):
        schedules = self._load_schedules()
        current_hour = now.hour
        current_minute = now.minute
        triggered = []

        for schedule in schedules:
            if not schedule.get('enabled', True):
                continue

            schedule_id = schedule['id']
            if schedule_id in self._triggered_schedules:
                continue

            try:
                wake_time_str = schedule['wake_time']
                wake_hour, wake_minute = map(int, wake_time_str.split(':'))

                if wake_hour == current_hour and wake_minute == current_minute:
                    self._triggered_schedules.add(schedule_id)
                    triggered.append(schedule)
            except (ValueError, KeyError) as e:
                print(f"Error parsing schedule {schedule_id}: {e}")

        return triggered

    def _execute_wake(self, schedule):
        device = self.device_manager.get_device(schedule['device_id'])
        if not device:
            return

        try:
            success = WOLSender.send_magic_packet(device['mac'])
            if success:
                self.wake_triggered.emit(schedule['id'], device['name'])

            if schedule.get('repeat') == 'once':
                self.device_manager.update_schedule(schedule['id'], enabled=False)
                self.refresh_schedules()
                self.schedule_completed.emit(schedule['id'])
        except Exception as e:
            print(f"Error executing wake for schedule {schedule['id']}: {e}")

    def run(self):
        while not self._stop_flag:
            now = datetime.now()

            self._check_date_change()

            current_minute = now.minute
            if current_minute != self._last_check_minute:
                self._last_check_minute = current_minute
                triggered = self._get_schedules_for_now(now)
                for schedule in triggered:
                    self._execute_wake(schedule)

            sleep_time = 60 - now.second
            if sleep_time <= 0:
                sleep_time = 1

            for _ in range(min(sleep_time, 10)):
                if self._stop_flag:
                    break
                time.sleep(1)
