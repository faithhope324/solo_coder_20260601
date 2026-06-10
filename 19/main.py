import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import sys
from typing import Optional

from event_store import Macro, MacroEvent, EventType, MouseButton
from keyboard_listener import InputListener
from json_serializer import JsonSerializer
from player import MacroPlayer
from tray_icon import TrayIcon


class MacroRecorderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("键盘宏录制器")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)

        self.current_macro: Optional[Macro] = None
        self.listener = InputListener()
        self.player = MacroPlayer()
        self.tray = TrayIcon()
        self.stop_hotkey = tk.StringVar(value="<ctrl>+<f6>")
        self.record_mouse_var = tk.BooleanVar(value=False)
        self.loop_count_var = tk.StringVar(value="1")
        self.infinite_loop_var = tk.BooleanVar(value=False)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.start_minimized_var = tk.BooleanVar(value=False)

        self._setup_tray_callbacks()
        self._setup_player_callbacks()
        self._setup_listener_callback()
        self._create_ui()

        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _setup_tray_callbacks(self):
        self.tray.set_callbacks(
            show_window=self._show_window,
            stop_playback=self._stop_playback,
            exit_app=self._exit_app
        )

    def _setup_player_callbacks(self):
        self.player.set_stop_callback(self._on_playback_stopped)
        self.player.set_progress_callback(self._on_playback_progress)

    def _setup_listener_callback(self):
        self.listener.set_event_callback(self._on_new_event)

    def _create_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(top_frame, text="⌨️  键盘宏录制器", font=("Segoe UI", 16, "bold"))
        title_label.pack(side=tk.LEFT)

        status_frame = ttk.Frame(top_frame)
        status_frame.pack(side=tk.RIGHT)
        self.status_label = ttk.Label(status_frame, text="就绪", foreground="gray")
        self.status_label.pack()

        controls_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill=tk.X)

        self.btn_start = ttk.Button(buttons_frame, text="🎬 开始录制", command=self._start_recording, width=15)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(buttons_frame, text="⏹️ 停止录制", command=self._stop_recording, state=tk.DISABLED, width=15)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_play = ttk.Button(buttons_frame, text="▶️ 播放宏", command=self._play_macro, width=15)
        self.btn_play.pack(side=tk.LEFT, padx=5)

        self.btn_stop_play = ttk.Button(buttons_frame, text="⏸️ 停止播放", command=self._stop_playback, state=tk.DISABLED, width=15)
        self.btn_stop_play.pack(side=tk.LEFT, padx=5)

        options_frame = ttk.Frame(controls_frame)
        options_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Checkbutton(options_frame, text="录制鼠标事件", variable=self.record_mouse_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(options_frame, text="循环次数:").pack(side=tk.LEFT, padx=(20, 5))
        self.loop_spinbox = ttk.Spinbox(options_frame, from_=1, to=100, width=5, textvariable=self.loop_count_var)
        self.loop_spinbox.pack(side=tk.LEFT)

        ttk.Checkbutton(options_frame, text="无限循环", variable=self.infinite_loop_var, command=self._toggle_infinite_loop).pack(side=tk.LEFT, padx=10)

        ttk.Label(options_frame, text="播放速度:").pack(side=tk.LEFT, padx=(20, 5))
        self.speed_combo = ttk.Combobox(options_frame, values=["0.5x", "1.0x", "1.5x", "2.0x", "3.0x"], width=6, state="readonly")
        self.speed_combo.set("1.0x")
        self.speed_combo.pack(side=tk.LEFT)
        self.speed_combo.bind("<<ComboboxSelected>>", self._on_speed_change)

        hotkey_frame = ttk.Frame(controls_frame)
        hotkey_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(hotkey_frame, text="停止热键:").pack(side=tk.LEFT, padx=5)
        self.hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey, width=15)
        self.hotkey_entry.pack(side=tk.LEFT)

        ttk.Button(hotkey_frame, text="设置", command=self._set_stop_hotkey, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(hotkey_frame, text="启动后最小化到托盘", variable=self.start_minimized_var).pack(side=tk.LEFT, padx=20)

        file_frame = ttk.LabelFrame(main_frame, text="宏文件管理", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(file_frame, text="📂 加载宏", command=self._load_macro, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="💾 保存宏", command=self._save_macro, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="🆕 新建宏", command=self._new_macro, width=12).pack(side=tk.LEFT, padx=5)

        self.macro_name_label = ttk.Label(file_frame, text="当前宏: 未命名宏", foreground="blue")
        self.macro_name_label.pack(side=tk.LEFT, padx=20)

        events_frame = ttk.LabelFrame(main_frame, text="宏事件列表 (支持编辑)", padding="10")
        events_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        list_frame = ttk.Frame(events_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("index", "event", "delay")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("index", text="#")
        self.tree.heading("event", text="事件")
        self.tree.heading("delay", text="延迟 (ms)")
        self.tree.column("index", width=50, anchor=tk.CENTER)
        self.tree.column("event", width=600, anchor=tk.W)
        self.tree.column("delay", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        edit_frame = ttk.Frame(events_frame)
        edit_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(edit_frame, text="🗑️ 删除选中", command=self._delete_selected, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_frame, text="✏️ 修改延迟", command=self._edit_delay, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_frame, text="➕ 插入按键", command=self._insert_key, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_frame, text="🔄 清空所有", command=self._clear_all_events, width=12).pack(side=tk.LEFT, padx=5)

        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5)
        self.progress_label = ttk.Label(self.progress_frame, text="", anchor=tk.CENTER)
        self.progress_label.pack(fill=tk.X, pady=(5, 0))

        self._new_macro()

    def _toggle_infinite_loop(self):
        if self.infinite_loop_var.get():
            self.loop_spinbox.configure(state=tk.DISABLED)
        else:
            self.loop_spinbox.configure(state=tk.NORMAL)

    def _on_speed_change(self, event):
        speed_text = self.speed_combo.get()
        self.speed_var.set(float(speed_text.replace("x", "")))

    def _set_stop_hotkey(self):
        hotkey = self.stop_hotkey.get().strip()
        if not hotkey:
            messagebox.showwarning("提示", "请输入有效的热键组合，例如: <ctrl>+<f6>")
            return
        try:
            self.player.set_stop_hotkey(hotkey)
            messagebox.showinfo("成功", f"停止热键已设置为: {hotkey}")
        except Exception as e:
            messagebox.showerror("错误", f"设置热键失败: {e}")

    def _start_recording(self):
        if self.player.is_playing():
            messagebox.showwarning("提示", "正在播放宏，请先停止播放")
            return

        macro_name = simpledialog.askstring("新建宏", "请输入宏名称:", initialvalue=self.current_macro.name if self.current_macro else "新宏")
        if not macro_name:
            return

        self.current_macro = self.listener.start_recording(macro_name, self.record_mouse_var.get())
        self._update_macro_name_label()

        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.btn_play.configure(state=tk.DISABLED)
        self.status_label.configure(text="🔴 正在录制...", foreground="red")
        self._clear_event_list()
        self.tray.notify("键盘宏录制器", "开始录制...")

    def _stop_recording(self):
        macro = self.listener.stop_recording()
        if macro:
            self.current_macro = macro
            self._refresh_event_list()
            self._update_macro_name_label()

        self.btn_start.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)
        self.btn_play.configure(state=tk.NORMAL if self.current_macro and len(self.current_macro.events) > 0 else tk.DISABLED)
        self.status_label.configure(text=f"✅ 录制完成，共 {len(self.current_macro.events) if self.current_macro else 0} 条事件", foreground="green")
        self.tray.notify("键盘宏录制器", f"录制完成，共 {len(self.current_macro.events) if self.current_macro else 0} 条事件")

    def _on_new_event(self, event: MacroEvent):
        self.root.after(0, self._add_event_to_list, event)

    def _add_event_to_list(self, event: MacroEvent):
        idx = len(self.current_macro.events) if self.current_macro else 0
        self.tree.insert("", tk.END, values=(idx, event.get_display_name(), event.delay_ms))

    def _play_macro(self):
        if not self.current_macro or len(self.current_macro.events) == 0:
            messagebox.showwarning("提示", "没有可播放的宏事件")
            return

        if self.listener.is_recording():
            messagebox.showwarning("提示", "正在录制中，请先停止录制")
            return

        loops = -1 if self.infinite_loop_var.get() else int(self.loop_count_var.get())
        speed = self.speed_var.get()

        self.player.set_stop_hotkey(self.stop_hotkey.get())
        self.player.play(self.current_macro, loops=loops, speed_multiplier=speed)

        self.btn_play.configure(state=tk.DISABLED)
        self.btn_stop_play.configure(state=tk.NORMAL)
        self.btn_start.configure(state=tk.DISABLED)
        self.status_label.configure(text="▶️ 正在播放...", foreground="blue")
        self.progress_bar.configure(maximum=len(self.current_macro.events))
        self.tray.notify("键盘宏录制器", "开始播放宏...")

    def _stop_playback(self):
        self.player.stop()
        self._on_playback_stopped()

    def _on_playback_stopped(self):
        self.root.after(0, self._update_ui_after_stop)

    def _update_ui_after_stop(self):
        self.btn_play.configure(state=tk.NORMAL if self.current_macro and len(self.current_macro.events) > 0 else tk.DISABLED)
        self.btn_stop_play.configure(state=tk.DISABLED)
        self.btn_start.configure(state=tk.NORMAL)
        self.status_label.configure(text="⏹️ 播放已停止", foreground="orange")
        self.progress_bar.configure(value=0)
        self.progress_label.configure(text="")
        self.tray.notify("键盘宏录制器", "播放已停止")

    def _on_playback_progress(self, loop: int, event_idx: int, total_events: int):
        self.root.after(0, self._update_progress, loop, event_idx, total_events)

    def _update_progress(self, loop: int, event_idx: int, total_events: int):
        self.progress_bar.configure(value=event_idx)
        loop_text = "无限" if self.infinite_loop_var.get() else self.loop_count_var.get()
        self.progress_label.configure(text=f"第 {loop}/{loop_text} 次循环 - 事件 {event_idx}/{total_events}")

        for iid in self.tree.get_children():
            self.tree.item(iid, tags=())
        items = self.tree.get_children()
        if 0 <= event_idx - 1 < len(items):
            self.tree.item(items[event_idx - 1], tags=("highlight",))
        self.tree.tag_configure("highlight", background="#e6f3ff")

    def _refresh_event_list(self):
        self._clear_event_list()
        if self.current_macro:
            for i, event in enumerate(self.current_macro.events):
                self.tree.insert("", tk.END, values=(i + 1, event.get_display_name(), event.delay_ms))

    def _clear_event_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _update_macro_name_label(self):
        if self.current_macro:
            mouse_text = " (含鼠标)" if self.current_macro.record_mouse else ""
            self.macro_name_label.configure(text=f"当前宏: {self.current_macro.name} - {len(self.current_macro.events)} 条事件{mouse_text}")

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的事件")
            return

        indices = []
        for item in selected:
            values = self.tree.item(item, "values")
            indices.append(int(values[0]) - 1)

        indices.sort(reverse=True)
        for idx in indices:
            if self.current_macro:
                self.current_macro.remove_event(idx)

        self._refresh_event_list()
        self._update_macro_name_label()
        self.btn_play.configure(state=tk.NORMAL if self.current_macro and len(self.current_macro.events) > 0 else tk.DISABLED)

    def _edit_delay(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改延迟的事件")
            return

        if len(selected) > 1:
            messagebox.showwarning("提示", "请只选择一个事件进行修改")
            return

        item = selected[0]
        values = self.tree.item(item, "values")
        idx = int(values[0]) - 1
        current_delay = int(values[2])

        new_delay = simpledialog.askinteger("修改延迟", "请输入新的延迟时间 (毫秒):", initialvalue=current_delay, minvalue=0, maxvalue=100000)
        if new_delay is not None and self.current_macro:
            self.current_macro.update_event_delay(idx, new_delay)
            self._refresh_event_list()

    def _insert_key(self):
        selected = self.tree.selection()
        insert_idx = len(self.current_macro.events) if self.current_macro else 0

        if selected:
            values = self.tree.item(selected[0], "values")
            insert_idx = int(values[0]) - 1

        key_name = simpledialog.askstring("插入按键", "请输入按键名称 (如 'a', 'Key.enter', 'Key.ctrl'):")
        if not key_name:
            return

        delay = simpledialog.askinteger("设置延迟", "请输入延迟时间 (毫秒):", initialvalue=100, minvalue=0, maxvalue=100000)
        if delay is None:
            return

        is_combination = messagebox.askyesno("组合键", "是否为组合键?")
        combination_keys = []
        if is_combination:
            keys_str = simpledialog.askstring("组合键", "请输入组合键列表，用逗号分隔 (如 'Key.ctrl,Key.shift,c'):")
            if keys_str:
                combination_keys = [k.strip() for k in keys_str.split(",")]

        event = MacroEvent(
            event_type=EventType.KEY_PRESS,
            delay_ms=delay,
            key=key_name if not is_combination else None,
            is_combination=is_combination,
            combination_keys=combination_keys
        )

        if self.current_macro:
            self.current_macro.insert_event(insert_idx, event)
            self._refresh_event_list()
            self._update_macro_name_label()
            self.btn_play.configure(state=tk.NORMAL)

    def _clear_all_events(self):
        if not self.current_macro or len(self.current_macro.events) == 0:
            return

        if messagebox.askyesno("确认", "确定要清空所有事件吗？"):
            self.current_macro.clear()
            self._refresh_event_list()
            self._update_macro_name_label()
            self.btn_play.configure(state=tk.DISABLED)

    def _new_macro(self):
        if self.listener.is_recording():
            messagebox.showwarning("提示", "正在录制中，请先停止录制")
            return
        if self.player.is_playing():
            messagebox.showwarning("提示", "正在播放中，请先停止播放")
            return

        self.current_macro = Macro(name="未命名宏")
        self._refresh_event_list()
        self._update_macro_name_label()
        self.btn_play.configure(state=tk.DISABLED)
        self.status_label.configure(text="就绪", foreground="gray")

    def _save_macro(self):
        if not self.current_macro:
            messagebox.showwarning("提示", "没有可保存的宏")
            return

        if not self.current_macro.name or self.current_macro.name == "未命名宏":
            name = simpledialog.askstring("保存宏", "请输入宏名称:", initialvalue="新宏")
            if not name:
                return
            self.current_macro.name = name

        macros_dir = JsonSerializer.get_macros_directory()
        default_filename = f"{self.current_macro.name}.json"
        filepath = filedialog.asksaveasfilename(
            initialdir=macros_dir,
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            if JsonSerializer.save_macro(self.current_macro, filepath):
                self._update_macro_name_label()
                messagebox.showinfo("成功", f"宏已保存到: {filepath}")
            else:
                messagebox.showerror("错误", "保存宏失败")

    def _load_macro(self):
        if self.listener.is_recording():
            messagebox.showwarning("提示", "正在录制中，请先停止录制")
            return
        if self.player.is_playing():
            messagebox.showwarning("提示", "正在播放中，请先停止播放")
            return

        macros_dir = JsonSerializer.get_macros_directory()
        filepath = filedialog.askopenfilename(
            initialdir=macros_dir,
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            macro = JsonSerializer.load_macro(filepath)
            if macro:
                self.current_macro = macro
                self._refresh_event_list()
                self._update_macro_name_label()
                self.record_mouse_var.set(macro.record_mouse)
                self.btn_play.configure(state=tk.NORMAL if len(macro.events) > 0 else tk.DISABLED)
                self.status_label.configure(text=f"已加载宏: {macro.name}", foreground="green")
            else:
                messagebox.showerror("错误", "加载宏失败")

    def _show_window(self):
        self.root.after(0, self._deiconify_and_raise)

    def _deiconify_and_raise(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_window_close(self):
        if messagebox.askyesno("最小化", "是否最小化到系统托盘？\n点击'是'最小化，点击'否'退出程序"):
            self.root.withdraw()
            self.tray.notify("键盘宏录制器", "程序已最小化到系统托盘")
        else:
            self._exit_app()

    def _exit_app(self):
        try:
            self.listener.stop_recording()
        except:
            pass
        try:
            self.player.stop()
        except:
            pass
        try:
            self.tray.stop()
        except:
            pass
        self.root.after(0, self.root.destroy)

    def run(self):
        self.player.set_stop_hotkey(self.stop_hotkey.get())
        self.tray.run_in_thread()

        if self.start_minimized_var.get():
            self.root.after(100, lambda: self.root.withdraw())
            self.tray.notify("键盘宏录制器", "程序已启动，最小化到系统托盘")

        self.root.mainloop()


def main():
    app = MacroRecorderApp()
    app.run()


if __name__ == "__main__":
    main()
