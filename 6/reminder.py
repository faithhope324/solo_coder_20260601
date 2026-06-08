import tkinter as tk
from tkinter import messagebox
import threading
import sys
import platform
import os


def play_sound():
    system = platform.system()
    if system == 'Windows':
        try:
            import winsound
            winsound.Beep(1000, 500)
            winsound.Beep(800, 300)
            winsound.Beep(1200, 400)
        except Exception as e:
            print(f"播放声音失败: {e}")
    else:
        try:
            for _ in range(3):
                print('\a')
        except Exception as e:
            print(f"播放声音失败: {e}")


def show_reminder_window(title, description):
    def run():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.bell()

        top = tk.Toplevel(root)
        top.title("任务提醒")
        top.attributes('-topmost', True)
        top.geometry("400x250")
        top.resizable(False, False)

        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        top.geometry(f"400x250+{x}+{y}")

        frame = tk.Frame(top, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(
            frame,
            text=f"🔔 {title}",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#e74c3c"
        )
        title_label.pack(pady=(0, 15))

        if description:
            desc_label = tk.Label(
                frame,
                text=description,
                font=("Microsoft YaHei", 11),
                wraplength=360,
                justify=tk.LEFT
            )
            desc_label.pack(pady=(0, 20))

        def on_ok():
            top.destroy()
            root.destroy()

        ok_btn = tk.Button(
            frame,
            text="知道了",
            command=on_ok,
            font=("Microsoft YaHei", 10, "bold"),
            bg="#3498db",
            fg="white",
            width=12,
            height=2,
            relief=tk.FLAT
        )
        ok_btn.pack(pady=10)

        top.protocol("WM_DELETE_WINDOW", on_ok)
        top.focus_force()
        top.grab_set()

        sound_thread = threading.Thread(target=play_sound, daemon=True)
        sound_thread.start()

        root.mainloop()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
