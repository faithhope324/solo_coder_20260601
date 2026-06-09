import json
import os
import uuid
from datetime import datetime


class DeviceManager:
    def __init__(self, devices_file='devices.json', schedules_file='schedules.json'):
        self.devices_file = devices_file
        self.schedules_file = schedules_file
        self.devices = []
        self.schedules = []
        self.load_devices()
        self.load_schedules()

    def load_devices(self):
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r', encoding='utf-8') as f:
                    self.devices = json.load(f)
            except Exception as e:
                print(f"Error loading devices: {e}")
                self.devices = []
        else:
            self.devices = []

    def save_devices(self):
        try:
            with open(self.devices_file, 'w', encoding='utf-8') as f:
                json.dump(self.devices, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error saving devices: {e}")
            return False

    def add_device(self, name, mac, ip):
        device_id = str(uuid.uuid4())
        device = {
            'id': device_id,
            'name': name,
            'mac': mac,
            'ip': ip,
            'status': 'offline',
            'created_at': datetime.now().isoformat()
        }
        self.devices.append(device)
        self.save_devices()
        return device

    def update_device(self, device_id, name=None, mac=None, ip=None):
        for device in self.devices:
            if device['id'] == device_id:
                if name is not None:
                    device['name'] = name
                if mac is not None:
                    device['mac'] = mac
                if ip is not None:
                    device['ip'] = ip
                device['updated_at'] = datetime.now().isoformat()
                self.save_devices()
                return device
        return None

    def delete_device(self, device_id):
        for i, device in enumerate(self.devices):
            if device['id'] == device_id:
                self.devices.pop(i)
                self.save_devices()
                return True
        return False

    def get_device(self, device_id):
        for device in self.devices:
            if device['id'] == device_id:
                return device
        return None

    def get_all_devices(self):
        return self.devices

    def update_device_status(self, device_id, status):
        for device in self.devices:
            if device['id'] == device_id:
                device['status'] = status
                return True
        return False

    def load_schedules(self):
        if os.path.exists(self.schedules_file):
            try:
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    self.schedules = json.load(f)
            except Exception as e:
                print(f"Error loading schedules: {e}")
                self.schedules = []
        else:
            self.schedules = []

    def save_schedules(self):
        try:
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error saving schedules: {e}")
            return False

    def add_schedule(self, device_id, wake_time, repeat='once'):
        schedule_id = str(uuid.uuid4())
        schedule = {
            'id': schedule_id,
            'device_id': device_id,
            'wake_time': wake_time,
            'repeat': repeat,
            'enabled': True,
            'created_at': datetime.now().isoformat()
        }
        self.schedules.append(schedule)
        self.save_schedules()
        return schedule

    def update_schedule(self, schedule_id, wake_time=None, repeat=None, enabled=None):
        for schedule in self.schedules:
            if schedule['id'] == schedule_id:
                if wake_time is not None:
                    schedule['wake_time'] = wake_time
                if repeat is not None:
                    schedule['repeat'] = repeat
                if enabled is not None:
                    schedule['enabled'] = enabled
                schedule['updated_at'] = datetime.now().isoformat()
                self.save_schedules()
                return schedule
        return None

    def delete_schedule(self, schedule_id):
        for i, schedule in enumerate(self.schedules):
            if schedule['id'] == schedule_id:
                self.schedules.pop(i)
                self.save_schedules()
                return True
        return False

    def get_schedule(self, schedule_id):
        for schedule in self.schedules:
            if schedule['id'] == schedule_id:
                return schedule
        return None

    def get_all_schedules(self):
        return self.schedules

    def get_schedules_by_device(self, device_id):
        return [s for s in self.schedules if s['device_id'] == device_id]
