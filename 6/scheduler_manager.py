import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from database import Database
from reminder import show_reminder_window


class SchedulerManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
        return cls._instance

    def _init(self):
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self.db = Database()
        self._job_map = {}
        self._load_tasks()

    def _task_callback(self, task_id):
        task = self.db.get_task(task_id)
        if task:
            show_reminder_window(task['title'], task['description'])
            if task['task_type'] == 'once':
                self.db.toggle_task_enabled(task_id, False)

    def _load_tasks(self):
        tasks = self.db.get_enabled_tasks()
        for task in tasks:
            self._add_job(task)

    def _add_job(self, task):
        task_id = task['id']
        if str(task_id) in self._job_map:
            self.scheduler.remove_job(self._job_map[str(task_id)])

        trigger = self._create_trigger(task)
        if trigger is None:
            return

        job = self.scheduler.add_job(
            self._task_callback,
            trigger=trigger,
            args=[task_id],
            id=str(task_id),
            replace_existing=True
        )
        self._job_map[str(task_id)] = job.id

    def _create_trigger(self, task):
        task_type = task['task_type']
        try:
            if task_type == 'once':
                run_at = datetime.fromisoformat(task['run_at'])
                if run_at > datetime.now():
                    return DateTrigger(run_date=run_at)
                return None
            elif task_type == 'daily':
                return CronTrigger(
                    hour=task['cron_hour'],
                    minute=task['cron_minute']
                )
            elif task_type == 'weekly':
                return CronTrigger(
                    day_of_week=task['cron_day'],
                    hour=task['cron_hour'],
                    minute=task['cron_minute']
                )
            elif task_type == 'interval':
                return IntervalTrigger(seconds=task['interval_seconds'])
            return None
        except Exception as e:
            print(f"创建触发器失败: {e}")
            return None

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def add_task_schedule(self, task_id):
        task = self.db.get_task(task_id)
        if task and task['enabled']:
            self._add_job(task)

    def remove_task_schedule(self, task_id):
        job_id = self._job_map.pop(str(task_id), None)
        if job_id and self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def update_task_schedule(self, task_id):
        self.remove_task_schedule(task_id)
        task = self.db.get_task(task_id)
        if task and task['enabled']:
            self._add_job(task)

    def toggle_task(self, task_id, enabled):
        if enabled:
            self.add_task_schedule(task_id)
        else:
            self.remove_task_schedule(task_id)

    def get_next_run_time(self, task_id):
        job_id = self._job_map.get(str(task_id))
        if job_id:
            job = self.scheduler.get_job(job_id)
            if job:
                return job.next_run_time
        return None

    def get_jobs_info(self):
        return self.scheduler.get_jobs()
