import os
import time
from pathlib import Path
from threading import Thread
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent


class FileMonitorEvent:
    def __init__(self, event_type, src_path, dest_path=None, timestamp=None):
        self.event_type = event_type
        self.src_path = src_path
        self.dest_path = dest_path
        self.timestamp = timestamp or time.time()

    def to_dict(self):
        return {
            'event_type': self.event_type,
            'src_path': self.src_path,
            'dest_path': self.dest_path,
            'timestamp': self.timestamp,
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))
        }


class MonitorHandler(FileSystemEventHandler):
    def __init__(self, event_queue, exclude_dirs=None, exclude_extensions=None):
        self.event_queue = event_queue
        self.exclude_dirs = set(exclude_dirs or [])
        self.exclude_extensions = set(ext.lower() for ext in (exclude_extensions or []))
        self._recently_created = {}
        self._debounce_window = 2.0

    def _should_skip(self, path):
        if self.exclude_dirs:
            path_parts = Path(path).parts
            for exclude_dir in self.exclude_dirs:
                if exclude_dir in path_parts:
                    return True
        if self.exclude_extensions:
            ext = Path(path).suffix.lower()
            if ext in self.exclude_extensions:
                return True
        return False

    def _cleanup_recently_created(self):
        current_time = time.time()
        to_remove = [path for path, t in self._recently_created.items() 
                     if current_time - t > self._debounce_window]
        for path in to_remove:
            del self._recently_created[path]

    def on_created(self, event):
        if not event.is_directory and not self._should_skip(event.src_path):
            self._recently_created[event.src_path] = time.time()
            self.event_queue.put(FileMonitorEvent('created', event.src_path))

    def on_deleted(self, event):
        if not event.is_directory and not self._should_skip(event.src_path):
            self.event_queue.put(FileMonitorEvent('deleted', event.src_path))

    def on_modified(self, event):
        if not event.is_directory and not self._should_skip(event.src_path):
            self._cleanup_recently_created()
            if event.src_path in self._recently_created:
                return
            self.event_queue.put(FileMonitorEvent('modified', event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            src_skip = self._should_skip(event.src_path)
            dest_skip = self._should_skip(event.dest_path)
            if not src_skip or not dest_skip:
                self.event_queue.put(FileMonitorEvent('renamed', event.src_path, event.dest_path))


class FileSystemMonitor:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.observer = None
        self.watch_path = None
        self.is_running = False
        self.exclude_dirs = []
        self.exclude_extensions = []

    def start(self, path, exclude_dirs=None, exclude_extensions=None):
        if self.is_running:
            self.stop()
        
        self.watch_path = path
        self.exclude_dirs = exclude_dirs or []
        self.exclude_extensions = exclude_extensions or []
        
        event_handler = MonitorHandler(
            self.event_queue,
            exclude_dirs=self.exclude_dirs,
            exclude_extensions=self.exclude_extensions
        )
        
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()
        self.is_running = True

    def stop(self):
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            self.observer = None

    def update_filters(self, exclude_dirs=None, exclude_extensions=None):
        if self.is_running and self.watch_path:
            self.start(self.watch_path, exclude_dirs, exclude_extensions)
