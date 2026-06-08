import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import queue
import os
import sys
from file_monitor import FileSystemMonitor
from event_processor import EventProcessor
from notifier import ScriptNotifier, EmailNotifier


def enable_dpi_awareness():
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class FolderMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件夹监控工具")
        self.root.geometry("1000x700")
        
        self.event_queue = queue.Queue()
        self.file_monitor = FileSystemMonitor(self.event_queue)
        self.event_processor = EventProcessor(self.event_queue)
        
        self.script_notifier = None
        self.email_notifier = None
        
        self.watch_path = tk.StringVar()
        self.exclude_dirs = []
        self.exclude_extensions = []
        
        self._create_ui()
        self._setup_event_handling()
        
        self.event_processor.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self._create_path_frame(main_frame)
        self._create_filter_frame(main_frame)
        self._create_event_list(main_frame)
        self._create_notebook(main_frame)
        self._create_status_bar(main_frame)

    def _create_path_frame(self, parent):
        path_frame = ttk.LabelFrame(parent, text="监控路径", padding="10")
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="文件夹:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(path_frame, textvariable=self.watch_path, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(path_frame, text="浏览", command=self._browse_folder).grid(row=0, column=2, padx=5)
        
        self.start_btn = ttk.Button(path_frame, text="开始监控", command=self._start_monitoring)
        self.start_btn.grid(row=0, column=3, padx=5)
        
        self.stop_btn = ttk.Button(path_frame, text="停止监控", command=self._stop_monitoring, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=4, padx=5)

    def _create_filter_frame(self, parent):
        filter_frame = ttk.LabelFrame(parent, text="过滤设置", padding="10")
        filter_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)
        
        ttk.Label(filter_frame, text="排除子目录:").grid(row=0, column=0, sticky=tk.W)
        self.exclude_dirs_entry = ttk.Entry(filter_frame, width=30)
        self.exclude_dirs_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Label(filter_frame, text="(多个用逗号分隔，如: temp,log,.git)").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(filter_frame, text="排除扩展名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.exclude_ext_entry = ttk.Entry(filter_frame, width=30)
        self.exclude_ext_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Label(filter_frame, text="(多个用逗号分隔，如: .tmp,.log,.bak)").grid(row=1, column=2, sticky=tk.W)
        
        ttk.Button(filter_frame, text="应用过滤", command=self._apply_filters).grid(row=0, column=3, rowspan=2, padx=10)

    def _create_event_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="事件日志", padding="10")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
        
        columns = ('time', 'type', 'path', 'dest')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('time', text='时间')
        self.tree.heading('type', text='类型')
        self.tree.heading('path', text='源路径')
        self.tree.heading('dest', text='目标路径')
        
        self.tree.column('time', width=150, anchor='center')
        self.tree.column('type', width=80, anchor='center')
        self.tree.column('path', width=400)
        self.tree.column('dest', width=300)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        event_type_map = {
            'created': ('新增', '#4CAF50'),
            'modified': ('修改', '#2196F3'),
            'deleted': ('删除', '#F44336'),
            'renamed': ('重命名', '#FF9800')
        }
        for event_type, (display, color) in event_type_map.items():
            self.tree.tag_configure(event_type, foreground=color)
        
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky=tk.W)
        ttk.Button(btn_frame, text="清空日志", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出日志", command=self._export_log).pack(side=tk.LEFT, padx=5)

    def _create_notebook(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self._create_script_tab(notebook)
        self._create_email_tab(notebook)

    def _create_script_tab(self, notebook):
        script_frame = ttk.Frame(notebook, padding="10")
        notebook.add(script_frame, text="脚本通知")
        
        self.script_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(script_frame, text="启用脚本通知", variable=self.script_enabled, command=self._toggle_script_notifier).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(script_frame, text="脚本路径:").grid(row=1, column=0, sticky=tk.W)
        self.script_path = tk.StringVar()
        ttk.Entry(script_frame, textvariable=self.script_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(script_frame, text="浏览", command=self._browse_script).grid(row=1, column=2)
        
        ttk.Label(script_frame, text="触发事件:").grid(row=2, column=0, sticky=tk.W, pady=10)
        event_frame = ttk.Frame(script_frame)
        event_frame.grid(row=2, column=1, sticky=tk.W, pady=10)
        
        self.script_on_created = tk.BooleanVar(value=True)
        self.script_on_modified = tk.BooleanVar(value=True)
        self.script_on_deleted = tk.BooleanVar(value=True)
        self.script_on_renamed = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(event_frame, text="新增", variable=self.script_on_created).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(event_frame, text="修改", variable=self.script_on_modified).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(event_frame, text="删除", variable=self.script_on_deleted).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(event_frame, text="重命名", variable=self.script_on_renamed).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(script_frame, text="应用设置", command=self._apply_script_settings).grid(row=3, column=0, columnspan=3, pady=10)

    def _create_email_tab(self, notebook):
        email_frame = ttk.Frame(notebook, padding="10")
        notebook.add(email_frame, text="邮件通知")
        
        self.email_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(email_frame, text="启用邮件通知", variable=self.email_enabled, command=self._toggle_email_notifier).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(email_frame, text="SMTP服务器:").grid(row=1, column=0, sticky=tk.W)
        self.smtp_server = tk.StringVar(value="smtp.gmail.com")
        ttk.Entry(email_frame, textvariable=self.smtp_server, width=30).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(email_frame, text="端口:").grid(row=1, column=2, sticky=tk.W)
        self.smtp_port = tk.StringVar(value="587")
        ttk.Entry(email_frame, textvariable=self.smtp_port, width=10).grid(row=1, column=3, padx=5, pady=2)
        
        ttk.Label(email_frame, text="用户名:").grid(row=2, column=0, sticky=tk.W)
        self.email_username = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_username, width=30).grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(email_frame, text="密码:").grid(row=2, column=2, sticky=tk.W)
        self.email_password = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_password, width=20, show="*").grid(row=2, column=3, padx=5, pady=2)
        
        ttk.Label(email_frame, text="发件人:").grid(row=3, column=0, sticky=tk.W)
        self.email_from = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_from, width=30).grid(row=3, column=1, padx=5, pady=2)
        
        ttk.Label(email_frame, text="收件人:").grid(row=3, column=2, sticky=tk.W)
        self.email_to = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_to, width=30).grid(row=3, column=3, padx=5, pady=2)
        
        ttk.Label(email_frame, text="触发事件:").grid(row=4, column=0, sticky=tk.W, pady=10)
        event_frame = ttk.Frame(email_frame)
        event_frame.grid(row=4, column=1, sticky=tk.W, pady=10)
        
        self.email_on_created = tk.BooleanVar(value=True)
        self.email_on_modified = tk.BooleanVar(value=False)
        self.email_on_deleted = tk.BooleanVar(value=True)
        self.email_on_renamed = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(event_frame, text="新增", variable=self.email_on_created).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(event_frame, text="修改", variable=self.email_on_modified).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(event_frame, text="删除", variable=self.email_on_deleted).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(event_frame, text="重命名", variable=self.email_on_renamed).pack(side=tk.LEFT, padx=5)
        
        btn_frame = ttk.Frame(email_frame)
        btn_frame.grid(row=5, column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="应用设置", command=self._apply_email_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="测试邮件", command=self._test_email).pack(side=tk.LEFT, padx=5)

    def _create_status_bar(self, parent):
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E))

    def _setup_event_handling(self):
        self.event_processor.set_ui_callback(self._on_file_event)

    def _on_file_event(self, event_dict):
        self.root.after(0, self._add_event_to_tree, event_dict)

    def _add_event_to_tree(self, event_dict):
        event_type = event_dict['event_type']
        values = (
            event_dict['time_str'],
            self._get_event_type_display(event_type),
            event_dict['src_path'],
            event_dict.get('dest_path', '')
        )
        self.tree.insert('', 0, values=values, tags=(event_type,))
        
        children = self.tree.get_children()
        if len(children) > 500:
            self.tree.delete(children[-1])

    def _get_event_type_display(self, event_type):
        mapping = {
            'created': '新增',
            'modified': '修改',
            'deleted': '删除',
            'renamed': '重命名'
        }
        return mapping.get(event_type, event_type)

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.watch_path.set(folder)

    def _browse_script(self):
        script = filedialog.askopenfilename(filetypes=[("所有文件", "*.*"), ("批处理", "*.bat;*.cmd"), ("Python", "*.py"), ("Shell", "*.sh")])
        if script:
            self.script_path.set(script)

    def _start_monitoring(self):
        path = self.watch_path.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("错误", "请选择有效的文件夹路径")
            return
        
        self._apply_filters()
        
        try:
            self.file_monitor.start(path, self.exclude_dirs, self.exclude_extensions)
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set(f"正在监控: {path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动监控失败: {e}")

    def _stop_monitoring(self):
        self.file_monitor.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("监控已停止")

    def _apply_filters(self):
        dirs_text = self.exclude_dirs_entry.get().strip()
        self.exclude_dirs = [d.strip() for d in dirs_text.split(',') if d.strip()] if dirs_text else []
        
        ext_text = self.exclude_ext_entry.get().strip()
        self.exclude_extensions = []
        if ext_text:
            for ext in ext_text.split(','):
                ext = ext.strip()
                if ext and not ext.startswith('.'):
                    ext = '.' + ext
                if ext:
                    self.exclude_extensions.append(ext.lower())
        
        if self.file_monitor.is_running:
            self.file_monitor.update_filters(self.exclude_dirs, self.exclude_extensions)
        
        self.status_var.set(f"过滤设置已应用 - 排除目录: {len(self.exclude_dirs)}个, 排除扩展名: {len(self.exclude_extensions)}个")

    def _clear_log(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.event_processor.clear_history()

    def _export_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("时间\t类型\t源路径\t目标路径\n")
                    f.write("="*100 + "\n")
                    for event in self.event_processor.get_history():
                        dest = event.get('dest_path', '')
                        f.write(f"{event['time_str']}\t{self._get_event_type_display(event['event_type'])}\t{event['src_path']}\t{dest}\n")
                messagebox.showinfo("成功", "日志已导出")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def _toggle_script_notifier(self):
        if self.script_enabled.get():
            self._apply_script_settings()
        else:
            if self.script_notifier:
                self.event_processor.remove_notification_callback(self.script_notifier.notify)
                self.script_notifier.set_enabled(False)

    def _apply_script_settings(self):
        script_path = self.script_path.get().strip()
        if not script_path or not os.path.isfile(script_path):
            if self.script_enabled.get():
                messagebox.showwarning("警告", "请选择有效的脚本文件")
            return
        
        event_types = []
        if self.script_on_created.get():
            event_types.append('created')
        if self.script_on_modified.get():
            event_types.append('modified')
        if self.script_on_deleted.get():
            event_types.append('deleted')
        if self.script_on_renamed.get():
            event_types.append('renamed')
        
        if self.script_notifier:
            self.event_processor.remove_notification_callback(self.script_notifier.notify)
        
        self.script_notifier = ScriptNotifier(script_path, event_types)
        self.script_notifier.set_enabled(self.script_enabled.get())
        self.event_processor.add_notification_callback(self.script_notifier.notify)
        
        self.status_var.set("脚本通知设置已应用")

    def _toggle_email_notifier(self):
        if self.email_enabled.get():
            self._apply_email_settings()
        else:
            if self.email_notifier:
                self.event_processor.remove_notification_callback(self.email_notifier.notify)
                self.email_notifier.set_enabled(False)

    def _apply_email_settings(self):
        if not self.email_enabled.get():
            return
        
        required_fields = [
            (self.smtp_server.get(), "SMTP服务器"),
            (self.smtp_port.get(), "端口"),
            (self.email_username.get(), "用户名"),
            (self.email_password.get(), "密码"),
            (self.email_from.get(), "发件人"),
            (self.email_to.get(), "收件人")
        ]
        
        for value, name in required_fields:
            if not value.strip():
                messagebox.showwarning("警告", f"请填写{name}")
                return
        
        event_types = []
        if self.email_on_created.get():
            event_types.append('created')
        if self.email_on_modified.get():
            event_types.append('modified')
        if self.email_on_deleted.get():
            event_types.append('deleted')
        if self.email_on_renamed.get():
            event_types.append('renamed')
        
        to_addrs = [addr.strip() for addr in self.email_to.get().split(',') if addr.strip()]
        
        if self.email_notifier:
            self.event_processor.remove_notification_callback(self.email_notifier.notify)
        
        try:
            self.email_notifier = EmailNotifier(
                smtp_server=self.smtp_server.get(),
                smtp_port=int(self.smtp_port.get()),
                username=self.email_username.get(),
                password=self.email_password.get(),
                from_addr=self.email_from.get(),
                to_addrs=to_addrs,
                enabled_event_types=event_types
            )
            self.email_notifier.set_enabled(self.email_enabled.get())
            self.event_processor.add_notification_callback(self.email_notifier.notify)
            self.status_var.set("邮件通知设置已应用")
        except Exception as e:
            messagebox.showerror("错误", f"配置失败: {e}")

    def _test_email(self):
        if not self.email_notifier:
            self._apply_email_settings()
        
        if self.email_notifier:
            test_event = {
                'event_type': 'created',
                'src_path': 'C:/test/test_file.txt',
                'dest_path': '',
                'time_str': '2024-01-01 12:00:00'
            }
            self.email_notifier.notify(test_event)
            messagebox.showinfo("提示", "测试邮件已发送，请查收")

    def _on_close(self):
        self.file_monitor.stop()
        self.event_processor.stop()
        self.root.destroy()


def main():
    enable_dpi_awareness()
    root = tk.Tk()
    app = FolderMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
