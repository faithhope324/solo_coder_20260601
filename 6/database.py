import sqlite3
from datetime import datetime
from threading import Lock


class Database:
    _instance = None
    _lock = Lock()

    def __new__(cls, db_path="tasks.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init(db_path)
        return cls._instance

    def _init(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                task_type TEXT NOT NULL,
                run_at TEXT NOT NULL,
                cron_day INTEGER,
                cron_hour INTEGER,
                cron_minute INTEGER,
                interval_seconds INTEGER,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_task(self, title, description, task_type, run_at,
                 cron_day=None, cron_hour=None, cron_minute=None,
                 interval_seconds=None, enabled=1):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, task_type, run_at,
                              cron_day, cron_hour, cron_minute,
                              interval_seconds, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, task_type, run_at,
              cron_day, cron_hour, cron_minute,
              interval_seconds, enabled))
        self.conn.commit()
        return cursor.lastrowid

    def update_task(self, task_id, title, description, task_type, run_at,
                    cron_day=None, cron_hour=None, cron_minute=None,
                    interval_seconds=None, enabled=1):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tasks SET title=?, description=?, task_type=?, run_at=?,
                   cron_day=?, cron_hour=?, cron_minute=?,
                   interval_seconds=?, enabled=?
            WHERE id=?
        ''', (title, description, task_type, run_at,
              cron_day, cron_hour, cron_minute,
              interval_seconds, enabled, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        self.conn.commit()

    def get_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
        return cursor.fetchone()

    def get_all_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        return cursor.fetchall()

    def get_enabled_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE enabled=1')
        return cursor.fetchall()

    def toggle_task_enabled(self, task_id, enabled):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE tasks SET enabled=? WHERE id=?',
                       (1 if enabled else 0, task_id))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
