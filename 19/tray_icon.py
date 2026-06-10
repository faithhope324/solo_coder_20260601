import threading
from typing import Callable, Optional
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw


class TrayIcon:
    def __init__(self):
        self._icon: Optional[Icon] = None
        self._show_window_callback: Optional[Callable[[], None]] = None
        self._stop_playback_callback: Optional[Callable[[], None]] = None
        self._exit_callback: Optional[Callable[[], None]] = None
        self._icon_thread: Optional[threading.Thread] = None
        self._is_running = False

    def set_callbacks(self,
                      show_window: Optional[Callable[[], None]] = None,
                      stop_playback: Optional[Callable[[], None]] = None,
                      exit_app: Optional[Callable[[], None]] = None):
        self._show_window_callback = show_window
        self._stop_playback_callback = stop_playback
        self._exit_callback = exit_app

    def _create_image(self) -> Image.Image:
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), (30, 30, 30))
        draw = ImageDraw.Draw(image)

        draw.rectangle([14, 14, 50, 48], outline=(255, 255, 255), width=2)

        for i in range(3):
            x1 = 18 + i * 10
            x2 = 25 + i * 10
            draw.rectangle([x1, 18, x2, 26], outline=(100, 200, 255), width=1)

        for i in range(3):
            x1 = 18 + i * 10
            x2 = 25 + i * 10
            draw.rectangle([x1, 29, x2, 37], outline=(100, 200, 255), width=1)

        for i in range(4):
            x1 = 15 + i * 9
            x2 = 22 + i * 9
            draw.rectangle([x1, 40, x2, 45], outline=(255, 150, 100), width=1)

        return image

    def _on_show_window(self, icon, item):
        if self._show_window_callback:
            self._show_window_callback()

    def _on_stop_playback(self, icon, item):
        if self._stop_playback_callback:
            self._stop_playback_callback()

    def _on_exit(self, icon, item):
        self._is_running = False
        if self._icon:
            self._icon.stop()
        if self._exit_callback:
            self._exit_callback()

    def run(self):
        if self._is_running:
            return

        menu = Menu(
            MenuItem('显示主窗口', self._on_show_window, default=True),
            MenuItem('停止播放', self._on_stop_playback),
            Menu.SEPARATOR,
            MenuItem('退出', self._on_exit)
        )

        self._icon = Icon(
            "keyboard_macro_recorder",
            self._create_image(),
            "键盘宏录制器",
            menu
        )

        self._is_running = True
        self._icon.run()

    def run_in_thread(self):
        if self._icon_thread and self._icon_thread.is_alive():
            return
        self._icon_thread = threading.Thread(target=self.run, daemon=True)
        self._icon_thread.start()

    def stop(self):
        self._is_running = False
        if self._icon:
            self._icon.stop()

    def notify(self, title: str, message: str):
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception as e:
                print(f"通知失败: {e}")
