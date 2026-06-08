import queue
import threading
import time


class EventProcessor:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.ui_callback = None
        self.notification_callbacks = []
        self.is_running = False
        self.processor_thread = None
        self.events_history = []
        self.max_history = 1000

    def set_ui_callback(self, callback):
        self.ui_callback = callback

    def add_notification_callback(self, callback):
        if callback not in self.notification_callbacks:
            self.notification_callbacks.append(callback)

    def remove_notification_callback(self, callback):
        if callback in self.notification_callbacks:
            self.notification_callbacks.remove(callback)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.processor_thread.start()

    def stop(self):
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=2)
            self.processor_thread = None

    def _process_loop(self):
        while self.is_running:
            try:
                event = self.event_queue.get(timeout=0.5)
                self._process_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing event: {e}")

    def _process_event(self, event):
        event_dict = event.to_dict()
        
        self.events_history.append(event_dict)
        if len(self.events_history) > self.max_history:
            self.events_history.pop(0)
        
        if self.ui_callback:
            try:
                self.ui_callback(event_dict)
            except Exception as e:
                print(f"UI callback error: {e}")
        
        for callback in self.notification_callbacks:
            try:
                callback(event_dict)
            except Exception as e:
                print(f"Notification callback error: {e}")

    def get_history(self):
        return self.events_history.copy()

    def clear_history(self):
        self.events_history.clear()
