import os
import subprocess
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


class ScriptNotifier:
    def __init__(self, script_path, enabled_event_types=None):
        self.script_path = script_path
        self.enabled_event_types = set(enabled_event_types or ['created', 'modified', 'deleted', 'renamed'])
        self.enabled = True

    def set_enabled(self, enabled):
        self.enabled = enabled

    def update_script(self, script_path):
        self.script_path = script_path

    def update_event_types(self, event_types):
        self.enabled_event_types = set(event_types)

    def notify(self, event_dict):
        if not self.enabled or not self.script_path:
            return
        if event_dict['event_type'] not in self.enabled_event_types:
            return
        
        def run_script():
            try:
                env = os.environ.copy()
                env['EVENT_TYPE'] = event_dict['event_type']
                env['SRC_PATH'] = event_dict['src_path']
                env['DEST_PATH'] = event_dict.get('dest_path', '')
                env['EVENT_TIME'] = event_dict['time_str']
                
                result = subprocess.run(
                    [self.script_path],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30
                )
                print(f"Script executed: {result.returncode}")
            except Exception as e:
                print(f"Script execution error: {e}")
        
        threading.Thread(target=run_script, daemon=True).start()


class EmailNotifier:
    def __init__(self, smtp_server, smtp_port, username, password, from_addr, to_addrs, enabled_event_types=None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs if isinstance(to_addrs, list) else [to_addrs]
        self.enabled_event_types = set(enabled_event_types or ['created', 'modified', 'deleted', 'renamed'])
        self.enabled = True
        self._last_send_time = 0
        self._min_interval = 5

    def set_enabled(self, enabled):
        self.enabled = enabled

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def update_event_types(self, event_types):
        self.enabled_event_types = set(event_types)

    def notify(self, event_dict):
        if not self.enabled:
            return
        if event_dict['event_type'] not in self.enabled_event_types:
            return
        
        import time
        current_time = time.time()
        if current_time - self._last_send_time < self._min_interval:
            return
        self._last_send_time = current_time
        
        def send_email():
            try:
                msg = MIMEMultipart()
                msg['From'] = Header(self.from_addr)
                msg['To'] = Header(', '.join(self.to_addrs))
                
                event_type_map = {
                    'created': '文件新增',
                    'modified': '文件修改',
                    'deleted': '文件删除',
                    'renamed': '文件重命名'
                }
                event_type_cn = event_type_map.get(event_dict['event_type'], event_dict['event_type'])
                subject = f"[文件监控] {event_type_cn}: {os.path.basename(event_dict['src_path'])}"
                msg['Subject'] = Header(subject, 'utf-8')
                
                body = f"""
文件监控通知
============

事件类型: {event_type_cn}
发生时间: {event_dict['time_str']}
源文件: {event_dict['src_path']}
"""
                if event_dict.get('dest_path'):
                    body += f"目标文件: {event_dict['dest_path']}\n"
                
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_addr, self.to_addrs, msg.as_string())
                server.quit()
                print("Email sent successfully")
            except Exception as e:
                print(f"Email send error: {e}")
        
        threading.Thread(target=send_email, daemon=True).start()
