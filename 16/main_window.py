from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QTimeEdit, QCheckBox, QGroupBox, QSplitter, QStatusBar,
    QAbstractItemView, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QColor, QBrush
from device_manager import DeviceManager
from wol_sender import WOLSender
from arp_scanner import ARPScanner
from ping_detector import PingDetector
from scheduler import WakeScheduler


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('网络唤醒工具 (Wake-on-LAN)')
        self.resize(1000, 600)

        self.device_manager = DeviceManager()
        self.arp_scanner = None
        self.ping_detector = None
        self.scheduler = None
        self.editing_device_id = None

        self.init_ui()
        self.init_threads()
        self.load_devices_to_table()
        self.load_schedules_to_list()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        splitter.addWidget(self.create_left_panel())
        splitter.addWidget(self.create_right_panel())
        splitter.setSizes([600, 400])

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')

    def create_left_panel(self):
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)

        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton('扫描局域网')
        self.scan_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.scan_btn)

        self.wake_selected_btn = QPushButton('批量唤醒选中')
        self.wake_selected_btn.clicked.connect(self.wake_selected_devices)
        btn_layout.addWidget(self.wake_selected_btn)

        self.refresh_btn = QPushButton('刷新状态')
        self.refresh_btn.clicked.connect(self.refresh_device_statuses)
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.device_table = QTableWidget()
        self.device_table.setColumnCount(5)
        self.device_table.setHorizontalHeaderLabels(
            ['', '设备名称', 'MAC 地址', 'IP 地址', '状态']
        )
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.device_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.device_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.device_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.device_table.cellClicked.connect(self.on_device_selected)
        self.device_table.cellDoubleClicked.connect(self.on_device_double_clicked)
        layout.addWidget(self.device_table)

        return left_widget

    def create_right_panel(self):
        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)

        form_group = QGroupBox('添加/编辑设备')
        form_layout = QVBoxLayout(form_group)

        layout.addWidget(form_group)

        name_layout = QHBoxLayout()
        name_label = QLabel('设备名称:')
        self.name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        form_layout.addLayout(name_layout)

        mac_layout = QHBoxLayout()
        mac_label = QLabel('MAC 地址:')
        self.mac_edit = QLineEdit()
        self.mac_edit.setPlaceholderText('00:11:22:33:44:55')
        mac_layout.addWidget(mac_label)
        mac_layout.addWidget(self.mac_edit)
        form_layout.addLayout(mac_layout)

        ip_layout = QHBoxLayout()
        ip_label = QLabel('IP 地址:')
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText('192.168.1.100')
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_edit)
        form_layout.addLayout(ip_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton('添加设备')
        self.add_btn.clicked.connect(self.add_or_update_device)
        btn_layout.addWidget(self.add_btn)

        self.clear_btn = QPushButton('清空表单')
        self.clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.clear_btn)
        form_layout.addLayout(btn_layout)

        self.delete_btn = QPushButton('删除当前设备')
        self.delete_btn.clicked.connect(self.delete_current_device)
        self.delete_btn.setEnabled(False)
        form_layout.addWidget(self.delete_btn)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        wake_group = QGroupBox('立即唤醒')
        wake_layout = QVBoxLayout(wake_group)
        self.wake_now_btn = QPushButton('立即唤醒当前设备')
        self.wake_now_btn.clicked.connect(self.wake_current_device)
        self.wake_now_btn.setEnabled(False)
        wake_layout.addWidget(self.wake_now_btn)
        layout.addWidget(wake_group)

        schedule_group = QGroupBox('定时唤醒')
        schedule_layout = QVBoxLayout(schedule_group)

        time_layout = QHBoxLayout()
        time_label = QLabel('唤醒时间:')
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat('HH:mm')
        self.time_edit.setTime(QTime.currentTime())
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        schedule_layout.addLayout(time_layout)

        repeat_layout = QHBoxLayout()
        repeat_label = QLabel('重复方式:')
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(['单次', '每天'])
        repeat_layout.addWidget(repeat_label)
        repeat_layout.addWidget(self.repeat_combo)
        schedule_layout.addLayout(repeat_layout)

        self.add_schedule_btn = QPushButton('添加定时任务')
        self.add_schedule_btn.clicked.connect(self.add_schedule)
        self.add_schedule_btn.setEnabled(False)
        schedule_layout.addWidget(self.add_schedule_btn)

        self.schedule_list_label = QLabel('定时任务列表:')
        schedule_layout.addWidget(self.schedule_list_label)

        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels(
            ['设备名称', '唤醒时间', '重复', '启用']
        )
        self.schedule_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.schedule_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.schedule_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.schedule_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        schedule_layout.addWidget(self.schedule_table)

        self.delete_schedule_btn = QPushButton('删除选中定时任务')
        self.delete_schedule_btn.clicked.connect(self.delete_selected_schedule)
        schedule_layout.addWidget(self.delete_schedule_btn)

        layout.addWidget(schedule_group)
        layout.addStretch()

        return right_widget

    def init_threads(self):
        self.ping_detector = PingDetector(self.device_manager, interval=60)
        self.ping_detector.status_updated.connect(self.on_status_updated)
        self.ping_detector.start()

        self.scheduler = WakeScheduler(self.device_manager)
        self.scheduler.wake_triggered.connect(self.on_wake_triggered)
        self.scheduler.schedule_completed.connect(self.on_schedule_completed)
        self.scheduler.start()

    def load_devices_to_table(self):
        self.device_table.setRowCount(0)
        devices = self.device_manager.get_all_devices()
        for device in devices:
            self.add_device_to_table(device)

    def add_device_to_table(self, device):
        row = self.device_table.rowCount()
        self.device_table.insertRow(row)

        checkbox = QCheckBox()
        self.device_table.setCellWidget(row, 0, checkbox)

        name_item = QTableWidgetItem(device['name'])
        name_item.setData(Qt.UserRole, device['id'])
        self.device_table.setItem(row, 1, name_item)

        mac_item = QTableWidgetItem(device['mac'])
        self.device_table.setItem(row, 2, mac_item)

        ip_item = QTableWidgetItem(device['ip'])
        self.device_table.setItem(row, 3, ip_item)

        status_item = QTableWidgetItem(device.get('status', 'offline'))
        self.update_status_color(status_item, device.get('status', 'offline'))
        self.device_table.setItem(row, 4, status_item)

    def update_status_color(self, item, status):
        if status == 'online':
            item.setForeground(QBrush(QColor(0, 128, 0)))
        elif status == 'offline':
            item.setForeground(QBrush(QColor(128, 128, 128)))
        else:
            item.setForeground(QBrush(QColor(128, 0, 0)))

    def on_device_selected(self, row, column):
        device_id = self.device_table.item(row, 1).data(Qt.UserRole)
        device = self.device_manager.get_device(device_id)
        if device:
            self.editing_device_id = device_id
            self.name_edit.setText(device['name'])
            self.mac_edit.setText(device['mac'])
            self.ip_edit.setText(device['ip'])
            self.add_btn.setText('更新设备')
            self.delete_btn.setEnabled(True)
            self.wake_now_btn.setEnabled(True)
            self.add_schedule_btn.setEnabled(True)
            self.load_schedules_for_device(device_id)

    def on_device_double_clicked(self, row, column):
        device_id = self.device_table.item(row, 1).data(Qt.UserRole)
        device = self.device_manager.get_device(device_id)
        if device:
            reply = QMessageBox.question(
                self, '确认唤醒',
                f'是否立即唤醒设备: {device["name"]}?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.wake_device(device)

    def add_or_update_device(self):
        name = self.name_edit.text().strip()
        mac = self.mac_edit.text().strip()
        ip = self.ip_edit.text().strip()

        if not name or not mac or not ip:
            QMessageBox.warning(self, '输入错误', '请填写所有字段')
            return

        if not WOLSender.validate_mac(mac):
            QMessageBox.warning(self, 'MAC 地址无效', '请输入有效的 MAC 地址')
            return

        if self.editing_device_id:
            device = self.device_manager.update_device(
                self.editing_device_id, name, mac, ip
            )
            if device:
                self.update_table_row(self.editing_device_id, device)
                QMessageBox.information(self, '成功', '设备更新成功')
                self.status_bar.showMessage(f'设备 {name} 已更新')
            self.clear_form()
        else:
            device = self.device_manager.add_device(name, mac, ip)
            if device:
                self.add_device_to_table(device)
                QMessageBox.information(self, '成功', '设备添加成功')
                self.status_bar.showMessage(f'设备 {name} 已添加')
                self.clear_form()

    def update_table_row(self, device_id, device):
        for row in range(self.device_table.rowCount()):
            item = self.device_table.item(row, 1)
            if item and item.data(Qt.UserRole) == device_id:
                self.device_table.item(row, 1).setText(device['name'])
                self.device_table.item(row, 2).setText(device['mac'])
                self.device_table.item(row, 3).setText(device['ip'])
                break

    def delete_current_device(self):
        if not self.editing_device_id:
            return

        device = self.device_manager.get_device(self.editing_device_id)
        if not device:
            return

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除设备: {device["name"]}?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            schedules = self.device_manager.get_schedules_by_device(self.editing_device_id)
            for s in schedules:
                self.device_manager.delete_schedule(s['id'])

            self.device_manager.delete_device(self.editing_device_id)
            self.load_devices_to_table()
            self.load_schedules_to_list()
            self.clear_form()
            self.status_bar.showMessage(f'设备 {device["name"]} 已删除')

    def clear_form(self):
        self.name_edit.clear()
        self.mac_edit.clear()
        self.ip_edit.clear()
        self.editing_device_id = None
        self.add_btn.setText('添加设备')
        self.delete_btn.setEnabled(False)
        self.wake_now_btn.setEnabled(False)
        self.add_schedule_btn.setEnabled(False)

    def start_scan(self):
        if self.arp_scanner and self.arp_scanner.isRunning():
            QMessageBox.information(self, '扫描中', '正在扫描局域网，请稍候...')
            return

        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage('正在扫描局域网...')

        self.arp_scanner = ARPScanner()
        self.arp_scanner.scan_finished.connect(self.on_scan_finished)
        self.arp_scanner.scan_progress.connect(self.on_scan_progress)
        self.arp_scanner.start()

    def on_scan_progress(self, current, total):
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)

    def on_scan_finished(self, devices):
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f'扫描完成，发现 {len(devices)} 个设备')

        if not devices:
            QMessageBox.information(self, '扫描结果', '未发现任何设备')
            return

        existing_ips = {d['ip'] for d in self.device_manager.get_all_devices()}
        new_devices = [d for d in devices if d['ip'] not in existing_ips]

        if not new_devices:
            QMessageBox.information(self, '扫描结果', f'发现 {len(devices)} 个设备，均已存在于列表中')
            return

        reply = QMessageBox.question(
            self, '扫描结果',
            f'发现 {len(devices)} 个设备，其中 {len(new_devices)} 个新设备。\n是否添加新设备到列表？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for device in new_devices:
                self.device_manager.add_device(device['name'], device['mac'], device['ip'])
            self.load_devices_to_table()
            self.status_bar.showMessage(f'已添加 {len(new_devices)} 个新设备')

    def refresh_device_statuses(self):
        if self.ping_detector and self.ping_detector.isRunning():
            self.status_bar.showMessage('正在刷新设备状态...')
            devices = self.device_manager.get_all_devices()
            for device in devices:
                if device.get('ip'):
                    self.ping_detector.check_device(device)
            self.status_bar.showMessage('设备状态刷新完成')

    def on_status_updated(self, device_id, status):
        for row in range(self.device_table.rowCount()):
            item = self.device_table.item(row, 1)
            if item and item.data(Qt.UserRole) == device_id:
                status_item = self.device_table.item(row, 4)
                status_item.setText(status)
                self.update_status_color(status_item, status)
                break

    def wake_current_device(self):
        if not self.editing_device_id:
            return

        device = self.device_manager.get_device(self.editing_device_id)
        if device:
            self.wake_device(device)

    def wake_device(self, device):
        success = WOLSender.send_magic_packet(device['mac'])
        if success:
            QMessageBox.information(self, '唤醒成功', f'已向设备 {device["name"]} 发送唤醒包')
            self.status_bar.showMessage(f'已唤醒设备: {device["name"]}')
        else:
            QMessageBox.warning(self, '唤醒失败', f'发送唤醒包失败，请检查网络设置')

    def wake_selected_devices(self):
        selected_devices = []
        for row in range(self.device_table.rowCount()):
            checkbox = self.device_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                device_id = self.device_table.item(row, 1).data(Qt.UserRole)
                device = self.device_manager.get_device(device_id)
                if device:
                    selected_devices.append(device)

        if not selected_devices:
            QMessageBox.information(self, '提示', '请先勾选要唤醒的设备')
            return

        reply = QMessageBox.question(
            self, '确认批量唤醒',
            f'确定要唤醒选中的 {len(selected_devices)} 个设备吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            macs = [d['mac'] for d in selected_devices]
            results = WOLSender.send_magic_packets(macs)
            success_count = sum(1 for v in results.values() if v)
            QMessageBox.information(
                self, '批量唤醒完成',
                f'成功唤醒 {success_count}/{len(selected_devices)} 个设备'
            )
            self.status_bar.showMessage(f'批量唤醒完成: {success_count}/{len(selected_devices)}')

    def add_schedule(self):
        if not self.editing_device_id:
            QMessageBox.warning(self, '提示', '请先选择一个设备')
            return

        wake_time = self.time_edit.time().toString('HH:mm')
        repeat = 'once' if self.repeat_combo.currentText() == '单次' else 'daily'

        schedule = self.device_manager.add_schedule(
            self.editing_device_id, wake_time, repeat
        )
        if schedule:
            self.load_schedules_to_list()
            QMessageBox.information(self, '成功', '定时任务添加成功')
            self.status_bar.showMessage(f'定时任务已添加: {wake_time}')

    def load_schedules_to_list(self):
        self.schedule_table.setRowCount(0)
        schedules = self.device_manager.get_all_schedules()
        for schedule in schedules:
            self.add_schedule_to_table(schedule)

    def load_schedules_for_device(self, device_id):
        self.schedule_table.setRowCount(0)
        schedules = self.device_manager.get_schedules_by_device(device_id)
        for schedule in schedules:
            self.add_schedule_to_table(schedule)

    def add_schedule_to_table(self, schedule):
        device = self.device_manager.get_device(schedule['device_id'])
        if not device:
            return

        row = self.schedule_table.rowCount()
        self.schedule_table.insertRow(row)

        name_item = QTableWidgetItem(device['name'])
        name_item.setData(Qt.UserRole, schedule['id'])
        self.schedule_table.setItem(row, 0, name_item)

        time_item = QTableWidgetItem(schedule['wake_time'])
        self.schedule_table.setItem(row, 1, time_item)

        repeat_text = '单次' if schedule.get('repeat') == 'once' else '每天'
        repeat_item = QTableWidgetItem(repeat_text)
        self.schedule_table.setItem(row, 2, repeat_item)

        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(schedule.get('enabled', True))
        enabled_checkbox.stateChanged.connect(
            lambda state, sid=schedule['id']: self.toggle_schedule(sid, state)
        )
        self.schedule_table.setCellWidget(row, 3, enabled_checkbox)

    def toggle_schedule(self, schedule_id, state):
        enabled = state == Qt.Checked
        self.device_manager.update_schedule(schedule_id, enabled=enabled)

    def delete_selected_schedule(self):
        current_row = self.schedule_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, '提示', '请先选择要删除的定时任务')
            return

        schedule_id = self.schedule_table.item(current_row, 0).data(Qt.UserRole)
        schedule = self.device_manager.get_schedule(schedule_id)
        if schedule:
            device = self.device_manager.get_device(schedule['device_id'])
            device_name = device['name'] if device else '未知设备'

            reply = QMessageBox.question(
                self, '确认删除',
                f'确定要删除设备 {device_name} 的定时任务吗？',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.device_manager.delete_schedule(schedule_id)
                if self.editing_device_id:
                    self.load_schedules_for_device(self.editing_device_id)
                else:
                    self.load_schedules_to_list()
                self.status_bar.showMessage('定时任务已删除')

    def on_wake_triggered(self, schedule_id, device_name):
        self.status_bar.showMessage(f'定时唤醒已触发: {device_name}')

    def on_schedule_completed(self, schedule_id):
        self.load_schedules_to_list()
        if self.editing_device_id:
            self.load_schedules_for_device(self.editing_device_id)

    def closeEvent(self, event):
        if self.arp_scanner and self.arp_scanner.isRunning():
            self.arp_scanner.stop()
            self.arp_scanner.wait()

        if self.ping_detector and self.ping_detector.isRunning():
            self.ping_detector.stop()
            self.ping_detector.wait()

        if self.scheduler and self.scheduler.isRunning():
            self.scheduler.stop()
            self.scheduler.wait()

        event.accept()
