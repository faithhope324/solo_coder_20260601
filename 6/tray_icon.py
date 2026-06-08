import threading
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self._stop_event = threading.Event()
        self._tray_thread = None

    def _create_image(self):
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), (52, 152, 219))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=(255, 255, 255))
        draw.ellipse((16, 16, 48, 48), fill=(231, 76, 60))
        draw.rectangle((30, 20, 34, 36), fill=(255, 255, 255))
        draw.rectangle((30, 34, 44, 38), fill=(255, 255, 255))
        return image

    def _on_show_window(self, icon, item):
        if self.app:
            self.app.show_window()

    def _on_exit(self, icon, item):
        self._stop_event.set()
        if self.app:
            self.app.quit_app()
        icon.stop()

    def _run(self):
        menu = pystray.Menu(
            item('显示主窗口', self._on_show_window, default=True),
            item('退出程序', self._on_exit)
        )
        self.icon = pystray.Icon(
            "task_scheduler",
            self._create_image(),
            "计划任务定时器",
            menu
        )
        self.icon.run()

    def start(self):
        if self._tray_thread is None or not self._tray_thread.is_alive():
            self._stop_event.clear()
            self._tray_thread = threading.Thread(target=self._run, daemon=True)
            self._tray_thread.start()

    def stop(self):
        self._stop_event.set()
        if self.icon:
            self.icon.stop()

    def notify(self, message, title="任务提醒"):
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                print(f"托盘通知失败: {e}")
