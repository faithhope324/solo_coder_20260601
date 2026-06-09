import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from wol_sender import WOLSender


class WakeScheduler(QThread):
    wake_triggered = pyqtSignal(str, str)
    schedule_completed = pyqtSignal(str)

    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self._stop_flag = False
        self._triggered_schedules = set()

    def stop(self):
        self._stop_flag = True

    def check_schedules(self):
        now = datetime.now()
        schedules = self.device_manager.get_all_schedules()
        triggered = []

        for schedule in schedules:
            if not schedule.get('enabled', True):
                continue

            try:
                wake_time = datetime.strptime(schedule['wake_time'], '%H:%M')
                wake_today = now.replace(
                    hour=wake_time.hour,
                    minute=wake_time.minute,
                    second=0,
                    microsecond=0
                )

                time_diff = (now - wake_today).total_seconds()

                if 0 <= time_diff < 60:
                    schedule_id = schedule['id']
                    if schedule_id not in self._triggered_schedules:
                        self._triggered_schedules.add(schedule_id)
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

    def run(self):
        while not self._stop_flag:
            now = datetime.now()

            if now.second == 0:
                self._triggered_schedules.clear()

            triggered_schedules = self.check_schedules()
            for schedule in triggered_schedules:
                self.execute_wake(schedule)

            time.sleep(1)
