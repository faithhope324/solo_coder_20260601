import tkinter as tk
import sys
import os
from task_manager_ui import TaskManagerUI
from scheduler_manager import SchedulerManager
from tray_icon import TrayIcon
from database import Database


class TaskSchedulerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.db = Database()
        self.scheduler = SchedulerManager()

        self.ui = TaskManagerUI(self.root, on_close_callback=self._on_window_close)
        self.tray = TrayIcon(self)

        self.scheduler.start()
        self.tray.start()

        self.ui.show_window()

    def _on_window_close(self):
        self.ui.hide_window()

    def show_window(self):
        self.ui.show_window()

    def quit_app(self):
        try:
            self.scheduler.shutdown()
            self.db.close()
        except Exception as e:
            print(f"清理资源时出错: {e}")

        try:
            if self.tray:
                self.tray.stop()
        except Exception as e:
            print(f"停止托盘时出错: {e}")

        try:
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"退出UI时出错: {e}")

        sys.exit(0)

    def run(self):
        self.root.mainloop()


def main():
    try:
        app = TaskSchedulerApp()
        app.run()
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
