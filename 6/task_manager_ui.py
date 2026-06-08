import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from calendar import monthrange
from database import Database
from scheduler_manager import SchedulerManager


WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
TASK_TYPES = [
    ("一次性倒计时", "once"),
    ("每天", "daily"),
    ("每周", "weekly"),
    ("间隔", "interval")
]


class DatePicker(tk.Toplevel):
    def __init__(self, parent, callback=None, initial_date=None):
        super().__init__(parent)
        self.title("选择日期")
        self.resizable(False, False)
        self.callback = callback
        self.result = None

        self.transient(parent)
        self.grab_set()

        if initial_date:
            self.current_date = initial_date
        else:
            self.current_date = date.today()

        self.year_var = tk.IntVar(value=self.current_date.year)
        self.month_var = tk.IntVar(value=self.current_date.month)

        self._build_ui()
        self._update_calendar()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 320) // 2
        self.geometry(f"300x320+{x}+{y}")

    def _build_ui(self):
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)

        ttk.Button(header_frame, text="◀", width=3, command=self._prev_month).pack(side=tk.LEFT)

        year_frame = ttk.Frame(header_frame)
        year_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Spinbox(year_frame, from_=2000, to=2100, width=6,
                    textvariable=self.year_var, command=self._update_calendar).pack(side=tk.LEFT, padx=5)
        ttk.Label(year_frame, text="年").pack(side=tk.LEFT)
        ttk.Spinbox(year_frame, from_=1, to=12, width=4,
                    textvariable=self.month_var, command=self._update_calendar).pack(side=tk.LEFT, padx=5)
        ttk.Label(year_frame, text="月").pack(side=tk.LEFT)

        ttk.Button(header_frame, text="▶", width=3, command=self._next_month).pack(side=tk.RIGHT)

        self.calendar_frame = ttk.Frame(self, padding=10)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True)

        days = ["日", "一", "二", "三", "四", "五", "六"]
        for i, d in enumerate(days):
            fg = "#e74c3c" if i in (0, 6) else "#333"
            ttk.Label(self.calendar_frame, text=d, font=("Microsoft YaHei", 10, "bold"),
                      foreground=fg, width=4, anchor=tk.CENTER).grid(row=0, column=i, padx=2, pady=5)

        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="今天", command=self._select_today).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="确定", command=self._on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _prev_month(self):
        month = self.month_var.get() - 1
        year = self.year_var.get()
        if month < 1:
            month = 12
            year -= 1
        self.month_var.set(month)
        self.year_var.set(year)
        self._update_calendar()

    def _next_month(self):
        month = self.month_var.get() + 1
        year = self.year_var.get()
        if month > 12:
            month = 1
            year += 1
        self.month_var.set(month)
        self.year_var.set(year)
        self._update_calendar()

    def _select_today(self):
        today = date.today()
        self.year_var.set(today.year)
        self.month_var.set(today.month)
        self.current_date = today
        self._update_calendar()

    def _update_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.destroy()

        year = self.year_var.get()
        month = self.month_var.get()
        first_day, num_days = monthrange(year, month)

        today = date.today()
        day = 1
        for week in range(1, 7):
            for col in range(7):
                if (week == 1 and col < first_day) or day > num_days:
                    continue
                current_date = date(year, month, day)
                is_today = current_date == today
                is_selected = current_date == self.current_date

                btn_text = str(day)
                if is_today:
                    btn_text = f"[{day}]"

                fg = "#e74c3c" if col in (0, 6) else "#333"
                bg = "#3498db" if is_selected else "#f0f0f0"
                fg_selected = "white" if is_selected else fg

                btn = tk.Button(self.calendar_frame, text=btn_text, width=4, height=1,
                                relief=tk.FLAT, font=("Microsoft YaHei", 10),
                                foreground=fg_selected, background=bg,
                                command=lambda d=current_date: self._select_date(d))
                btn.grid(row=week, column=col, padx=2, pady=2)
                day += 1

    def _select_date(self, d):
        self.current_date = d
        self._update_calendar()

    def _on_ok(self):
        self.result = self.current_date
        if self.callback:
            self.callback(self.current_date)
        self.destroy()


class TimePicker(tk.Toplevel):
    def __init__(self, parent, time_var=None):
        super().__init__(parent)
        self.title("选择时间")
        self.resizable(False, False)
        self.time_var = time_var

        self.transient(parent)
        self.grab_set()

        try:
            if time_var:
                current = datetime.strptime(time_var.get(), "%H:%M:%S")
            else:
                current = datetime.now()
        except ValueError:
            current = datetime.now()

        self.hour_var = tk.IntVar(value=current.hour)
        self.minute_var = tk.IntVar(value=current.minute)
        self.second_var = tk.IntVar(value=current.second)

        self._build_ui()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 280) // 2
        y = (screen_height - 180) // 2
        self.geometry(f"280x180+{x}+{y}")

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        time_frame = ttk.Frame(main_frame)
        time_frame.pack(pady=10)

        ttk.Spinbox(time_frame, from_=0, to=23, width=5,
                    textvariable=self.hour_var, font=("Microsoft YaHei", 14, "bold"),
                    format="%02.0f").pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":", font=("Microsoft YaHei", 14, "bold")).pack(side=tk.LEFT)
        ttk.Spinbox(time_frame, from_=0, to=59, width=5,
                    textvariable=self.minute_var, font=("Microsoft YaHei", 14, "bold"),
                    format="%02.0f").pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":", font=("Microsoft YaHei", 14, "bold")).pack(side=tk.LEFT)
        ttk.Spinbox(time_frame, from_=0, to=59, width=5,
                    textvariable=self.second_var, font=("Microsoft YaHei", 14, "bold"),
                    format="%02.0f").pack(side=tk.LEFT, padx=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="现在", command=self._set_now, width=8).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="确定", command=self._on_ok, width=8).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=8).pack(side=tk.LEFT, padx=10)

    def _set_now(self):
        now = datetime.now()
        self.hour_var.set(now.hour)
        self.minute_var.set(now.minute)
        self.second_var.set(now.second)

    def _on_ok(self):
        time_str = f"{self.hour_var.get():02d}:{self.minute_var.get():02d}:{self.second_var.get():02d}"
        if self.time_var:
            self.time_var.set(time_str)
        self.destroy()


class TaskDialog(tk.Toplevel):
    def __init__(self, parent, task=None, title="添加任务"):
        super().__init__(parent)
        self.title(title)
        self.geometry("560x540")
        self.resizable(False, False)
        self.result = None
        self.task = task

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 560) // 2
        y = (screen_height - 540) // 2
        self.geometry(f"560x540+{x}+{y}")

        self._build_ui()
        if task:
            self._load_task()

        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        padding = {"padx": 15, "pady": 8}
        entry_font = ("Microsoft YaHei", 10)
        label_font = ("Microsoft YaHei", 10, "bold")

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="任务标题:", font=label_font).grid(row=0, column=0, sticky="w", **padding)
        self.title_entry = ttk.Entry(main_frame, font=entry_font, width=35)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky="ew", **padding)

        ttk.Label(main_frame, text="任务描述:", font=label_font).grid(row=1, column=0, sticky="nw", **padding)
        self.desc_text = tk.Text(main_frame, font=entry_font, width=35, height=4, wrap=tk.WORD)
        self.desc_text.grid(row=1, column=1, columnspan=2, sticky="ew", **padding)

        ttk.Label(main_frame, text="任务类型:", font=label_font).grid(row=2, column=0, sticky="w", **padding)
        self.task_type_var = tk.StringVar(value="一次性倒计时")
        self.task_type_combo = ttk.Combobox(
            main_frame,
            textvariable=self.task_type_var,
            values=[t[0] for t in TASK_TYPES],
            state="readonly",
            font=entry_font,
            width=32
        )
        self.task_type_combo.grid(row=2, column=1, columnspan=2, sticky="ew", **padding)
        self.task_type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        self.once_frame = ttk.Frame(main_frame)
        self.once_frame.grid(row=3, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Label(self.once_frame, text="执行时间:", font=label_font).grid(row=0, column=0, sticky="w")
        now = datetime.now() + timedelta(minutes=1)
        self.date_var = tk.StringVar(value=now.strftime("%Y-%m-%d"))
        self.time_var = tk.StringVar(value=now.strftime("%H:%M:%S"))
        ttk.Entry(self.once_frame, textvariable=self.date_var, width=12, font=entry_font).grid(row=0, column=1, padx=5)
        ttk.Button(self.once_frame, text="📅", width=3, command=self._pick_date).grid(row=0, column=2, padx=2)
        ttk.Entry(self.once_frame, textvariable=self.time_var, width=10, font=entry_font).grid(row=0, column=3, padx=5)
        ttk.Button(self.once_frame, text="⏰", width=3, command=self._pick_time).grid(row=0, column=4, padx=2)

        self.daily_frame = ttk.Frame(main_frame)
        self.daily_frame.grid(row=4, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Label(self.daily_frame, text="执行时间:", font=label_font).grid(row=0, column=0, sticky="w")
        self.daily_hour_var = tk.StringVar(value="08")
        self.daily_minute_var = tk.StringVar(value="00")
        ttk.Spinbox(self.daily_frame, from_=0, to=23, width=5, textvariable=self.daily_hour_var, font=entry_font, format="%02.0f").grid(row=0, column=1, padx=5)
        ttk.Label(self.daily_frame, text=":", font=label_font).grid(row=0, column=2)
        ttk.Spinbox(self.daily_frame, from_=0, to=59, width=5, textvariable=self.daily_minute_var, font=entry_font, format="%02.0f").grid(row=0, column=3, padx=5)

        self.weekly_frame = ttk.Frame(main_frame)
        self.weekly_frame.grid(row=5, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Label(self.weekly_frame, text="星期:", font=label_font).grid(row=0, column=0, sticky="w")
        self.weekday_var = tk.StringVar(value="周一")
        ttk.Combobox(
            self.weekly_frame,
            textvariable=self.weekday_var,
            values=WEEKDAYS,
            state="readonly",
            font=entry_font,
            width=8
        ).grid(row=0, column=1, padx=5)
        ttk.Label(self.weekly_frame, text="时间:", font=label_font).grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.weekly_hour_var = tk.StringVar(value="08")
        self.weekly_minute_var = tk.StringVar(value="00")
        ttk.Spinbox(self.weekly_frame, from_=0, to=23, width=5, textvariable=self.weekly_hour_var, font=entry_font, format="%02.0f").grid(row=0, column=3, padx=2)
        ttk.Label(self.weekly_frame, text=":", font=label_font).grid(row=0, column=4)
        ttk.Spinbox(self.weekly_frame, from_=0, to=59, width=5, textvariable=self.weekly_minute_var, font=entry_font, format="%02.0f").grid(row=0, column=5, padx=2)

        self.interval_frame = ttk.Frame(main_frame)
        self.interval_frame.grid(row=6, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Label(self.interval_frame, text="间隔秒数:", font=label_font).grid(row=0, column=0, sticky="w")
        self.interval_var = tk.StringVar(value="60")
        ttk.Spinbox(self.interval_frame, from_=10, to=86400, width=15, textvariable=self.interval_var, font=entry_font).grid(row=0, column=1, padx=5)
        ttk.Label(self.interval_frame, text="秒", font=label_font).grid(row=0, column=2, sticky="w")

        self.enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(main_frame, text="启用任务", variable=self.enabled_var,
                       font=label_font, bg=main_frame.cget("bg"),
                       activebackground=main_frame.cget("bg"),
                       selectcolor=main_frame.cget("bg")).grid(row=7, column=0, columnspan=3, sticky="w", **padding)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="确定", command=self._on_ok, width=12).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self._on_cancel, width=12).pack(side=tk.LEFT, padx=10)

        self._on_type_change(None)

    def _on_type_change(self, event):
        task_type = self.task_type_var.get()
        type_map = {t[0]: t[1] for t in TASK_TYPES}
        type_val = type_map.get(task_type, "once")

        self.once_frame.grid_remove()
        self.daily_frame.grid_remove()
        self.weekly_frame.grid_remove()
        self.interval_frame.grid_remove()

        if type_val == "once":
            self.once_frame.grid()
        elif type_val == "daily":
            self.daily_frame.grid()
        elif type_val == "weekly":
            self.weekly_frame.grid()
        elif type_val == "interval":
            self.interval_frame.grid()

    def _load_task(self):
        task = self.task
        self.title_entry.insert(0, task["title"])
        if task["description"]:
            self.desc_text.insert("1.0", task["description"])

        type_map = {t[1]: t[0] for t in TASK_TYPES}
        self.task_type_var.set(type_map.get(task["task_type"], "一次性倒计时"))

        if task["task_type"] == "once":
            run_at = datetime.fromisoformat(task["run_at"])
            self.date_var.set(run_at.strftime("%Y-%m-%d"))
            self.time_var.set(run_at.strftime("%H:%M:%S"))
        elif task["task_type"] == "daily":
            self.daily_hour_var.set(f"{task['cron_hour']:02d}")
            self.daily_minute_var.set(f"{task['cron_minute']:02d}")
        elif task["task_type"] == "weekly":
            self.weekday_var.set(WEEKDAYS[task["cron_day"]])
            self.weekly_hour_var.set(f"{task['cron_hour']:02d}")
            self.weekly_minute_var.set(f"{task['cron_minute']:02d}")
        elif task["task_type"] == "interval":
            self.interval_var.set(str(task["interval_seconds"]))

        self.enabled_var.set(bool(task["enabled"]))
        self._on_type_change(None)

    def _on_ok(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("提示", "请输入任务标题", parent=self)
            return

        description = self.desc_text.get("1.0", tk.END).strip()
        type_map = {t[0]: t[1] for t in TASK_TYPES}
        task_type = type_map.get(self.task_type_var.get(), "once")

        run_at = ""
        cron_day = None
        cron_hour = None
        cron_minute = None
        interval_seconds = None

        try:
            if task_type == "once":
                run_at_str = f"{self.date_var.get()} {self.time_var.get()}"
                run_at = datetime.strptime(run_at_str, "%Y-%m-%d %H:%M:%S")
                if run_at < datetime.now():
                    messagebox.showwarning("提示", "执行时间必须大于当前时间", parent=self)
                    return
                run_at = run_at.isoformat()
            elif task_type == "daily":
                cron_hour = int(self.daily_hour_var.get())
                cron_minute = int(self.daily_minute_var.get())
                run_at = f"每天 {cron_hour:02d}:{cron_minute:02d}"
            elif task_type == "weekly":
                cron_day = WEEKDAYS.index(self.weekday_var.get())
                cron_hour = int(self.weekly_hour_var.get())
                cron_minute = int(self.weekly_minute_var.get())
                run_at = f"每周{WEEKDAYS[cron_day]} {cron_hour:02d}:{cron_minute:02d}"
            elif task_type == "interval":
                interval_seconds = int(self.interval_var.get())
                if interval_seconds < 10:
                    messagebox.showwarning("提示", "间隔时间不能小于10秒", parent=self)
                    return
                run_at = f"每 {interval_seconds} 秒"
        except ValueError as e:
            messagebox.showerror("错误", f"时间格式错误: {e}", parent=self)
            return

        self.result = {
            "title": title,
            "description": description,
            "task_type": task_type,
            "run_at": run_at,
            "cron_day": cron_day,
            "cron_hour": cron_hour,
            "cron_minute": cron_minute,
            "interval_seconds": interval_seconds,
            "enabled": 1 if self.enabled_var.get() else 0
        }
        self.destroy()

    def _pick_date(self):
        try:
            current_str = self.date_var.get()
            initial_date = datetime.strptime(current_str, "%Y-%m-%d").date()
        except ValueError:
            initial_date = date.today()

        def on_date_selected(selected_date):
            self.date_var.set(selected_date.strftime("%Y-%m-%d"))

        DatePicker(self, callback=on_date_selected, initial_date=initial_date)

    def _pick_time(self):
        TimePicker(self, time_var=self.time_var)

    def _on_cancel(self):
        self.result = None
        self.destroy()


class TaskManagerUI:
    def __init__(self, root, on_close_callback=None):
        self.root = root
        self.on_close_callback = on_close_callback
        self.db = Database()
        self.scheduler = SchedulerManager()
        self._build_ui()
        self.refresh_task_list()

    def _build_ui(self):
        self.root.title("计划任务定时器")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Microsoft YaHei", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 11, "bold"))
        style.configure("TButton", font=("Microsoft YaHei", 10), padding=8)
        style.configure("TLabel", font=("Microsoft YaHei", 10))

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="➕ 添加任务", command=self._on_add_task,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✏️ 编辑任务", command=self._on_edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 删除任务", command=self._on_delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 刷新列表", command=self.refresh_task_list).pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(btn_frame, textvariable=self.status_var,
                  font=("Microsoft YaHei", 9), foreground="#666").pack(side=tk.RIGHT, padx=10)

        columns = ("id", "title", "task_type", "run_at", "next_run", "status")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="browse")

        column_configs = [
            ("id", "ID", 60, tk.CENTER),
            ("title", "任务标题", 250, tk.W),
            ("task_type", "类型", 100, tk.CENTER),
            ("run_at", "执行时间", 200, tk.W),
            ("next_run", "下次执行", 180, tk.CENTER),
            ("status", "状态", 80, tk.CENTER)
        ]

        for col, text, width, anchor in column_configs:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._on_edit_task())

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _get_task_type_display(self, task_type):
        type_map = {t[1]: t[0] for t in TASK_TYPES}
        return type_map.get(task_type, task_type)

    def _format_run_at(self, run_at, task_type):
        if task_type == "once" and "T" in run_at:
            try:
                dt = datetime.fromisoformat(run_at)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return run_at.replace("T", " ")
        return run_at

    def refresh_task_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        tasks = self.db.get_all_tasks()
        type_map = {t[1]: t[0] for t in TASK_TYPES}

        for task in tasks:
            status_text = "✅ 启用" if task["enabled"] else "❌ 禁用"
            task_type_display = type_map.get(task["task_type"], task["task_type"])

            next_run = self.scheduler.get_next_run_time(task["id"])
            next_run_text = next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "-"

            run_at_display = self._format_run_at(task["run_at"], task["task_type"])

            self.tree.insert("", tk.END, values=(
                task["id"],
                task["title"],
                task_type_display,
                run_at_display,
                next_run_text,
                status_text
            ), tags=("enabled" if task["enabled"] else "disabled",))

        self.tree.tag_configure("disabled", foreground="#999")

        task_count = len(tasks)
        enabled_count = sum(1 for t in tasks if t["enabled"])
        self.status_var.set(f"共 {task_count} 个任务，已启用 {enabled_count} 个")

    def _get_selected_task_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个任务", parent=self.root)
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def _on_add_task(self):
        dialog = TaskDialog(self.root, title="添加任务")
        self.root.wait_window(dialog)
        if dialog.result:
            task_id = self.db.add_task(**dialog.result)
            if dialog.result["enabled"]:
                self.scheduler.add_task_schedule(task_id)
            self.refresh_task_list()

    def _on_edit_task(self):
        task_id = self._get_selected_task_id()
        if task_id is None:
            return

        task = self.db.get_task(task_id)
        if not task:
            return

        dialog = TaskDialog(self.root, task=task, title="编辑任务")
        self.root.wait_window(dialog)
        if dialog.result:
            self.db.update_task(task_id, **dialog.result)
            self.scheduler.update_task_schedule(task_id)
            self.refresh_task_list()

    def _on_delete_task(self):
        task_id = self._get_selected_task_id()
        if task_id is None:
            return

        task = self.db.get_task(task_id)
        if not task:
            return

        if messagebox.askyesno("确认", f"确定要删除任务「{task['title']}」吗？", parent=self.root):
            self.scheduler.remove_task_schedule(task_id)
            self.db.delete_task(task_id)
            self.refresh_task_list()

    def _on_close(self):
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.refresh_task_list()

    def hide_window(self):
        self.root.withdraw()
