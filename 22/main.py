import sys
import numpy as np
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox,
    QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

from audio_capture import AudioCapture, WavFileLoader, AudioPlayer, PYAUDIO_AVAILABLE, SOUNDDEVICE_AVAILABLE
from spectrum_analyzer import SpectrumAnalyzer, SpectrumCanvas
from waveform_plot import WaveformCanvas
from pitch_detector import PitchDetector


class AudioSpectrumAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.sample_rate = 44100
        self.chunk = 1024
        self.fft_size = 1024
        self.window_type = 'hann'
        self.mode = 'realtime'
        self.use_simulation = not (PYAUDIO_AVAILABLE or SOUNDDEVICE_AVAILABLE)

        self.audio_capture = None
        self.audio_player = None
        self.full_audio_data = None
        self.selected_audio_data = None
        self.selected_sample_rate = None
        self.pitch_buffer = np.zeros(4096, dtype=np.float32)

        self.spectrum_analyzer = SpectrumAnalyzer(
            sample_rate=self.sample_rate,
            fft_size=self.fft_size,
            window_type=self.window_type
        )
        self.pitch_detector = PitchDetector(sample_rate=self.sample_rate)

        self.init_ui()
        self.apply_style()

        if self.use_simulation:
            self.statusBar().showMessage('注意：未检测到音频库，将使用模拟数据模式', 10000)

    def init_ui(self):
        self.setWindowTitle('声音频谱分析工具')
        self.setGeometry(100, 100, 1100, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        self.waveform_canvas = WaveformCanvas(duration=2.0, sample_rate=self.sample_rate)
        waveform_group = QGroupBox('波形图 (时域)')
        waveform_layout = QVBoxLayout()
        waveform_layout.addWidget(self.waveform_canvas)
        waveform_group.setLayout(waveform_layout)
        self.set_groupbox_style(waveform_group)
        main_layout.addWidget(waveform_group, stretch=3)

        self.spectrum_canvas = SpectrumCanvas()
        spectrum_group = QGroupBox('频谱图 (频域)')
        spectrum_layout = QVBoxLayout()
        spectrum_layout.addWidget(self.spectrum_canvas)
        spectrum_group.setLayout(spectrum_layout)
        self.set_groupbox_style(spectrum_group)
        main_layout.addWidget(spectrum_group, stretch=4)

        pitch_panel = self.create_pitch_panel()
        main_layout.addWidget(pitch_panel)

        self.waveform_canvas.region_selected.connect(self.on_waveform_region_selected)
        self.spectrum_canvas.region_selected.connect(self.on_spectrum_region_selected)

        self.show_peaks = True

    def create_control_panel(self):
        panel = QGroupBox('控制面板')
        layout = QHBoxLayout()
        layout.setSpacing(15)

        btn_layout = QVBoxLayout()
        self.btn_start = QPushButton('开始录制')
        self.btn_start.clicked.connect(self.start_recording)
        self.btn_start.setMinimumHeight(35)

        self.btn_stop = QPushButton('停止')
        self.btn_stop.clicked.connect(self.stop_recording)
        self.btn_stop.setMinimumHeight(35)
        self.btn_stop.setEnabled(False)

        self.btn_load = QPushButton('加载 WAV 文件')
        self.btn_load.clicked.connect(self.load_wav_file)
        self.btn_load.setMinimumHeight(35)

        self.btn_play = QPushButton('播放选中区域')
        self.btn_play.clicked.connect(self.play_selection)
        self.btn_play.setMinimumHeight(35)
        self.btn_play.setEnabled(False)

        self.btn_analyze = QPushButton('分析选中区域')
        self.btn_analyze.clicked.connect(self.analyze_selection)
        self.btn_analyze.setMinimumHeight(35)
        self.btn_analyze.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(self.btn_analyze)
        layout.addLayout(btn_layout)

        param_layout = QGridLayout()
        param_layout.setHorizontalSpacing(10)
        param_layout.setVerticalSpacing(8)

        fft_label = QLabel('FFT 窗口大小:')
        self.fft_combo = QComboBox()
        self.fft_combo.addItems(['512', '1024', '2048'])
        self.fft_combo.setCurrentIndex(1)
        self.fft_combo.currentIndexChanged.connect(self.on_fft_size_changed)

        window_label = QLabel('窗函数:')
        self.window_combo = QComboBox()
        self.window_combo.addItem('汉宁窗', 'hann')
        self.window_combo.addItem('汉明窗', 'hamming')
        self.window_combo.addItem('矩形窗', 'rect')
        self.window_combo.currentIndexChanged.connect(self.on_window_changed)

        peaks_label = QLabel('峰值标记:')
        self.peaks_combo = QComboBox()
        self.peaks_combo.addItem('显示', True)
        self.peaks_combo.addItem('隐藏', False)
        self.peaks_combo.currentIndexChanged.connect(self.on_peaks_toggled)

        pitch_label = QLabel('基频检测:')
        self.pitch_combo = QComboBox()
        self.pitch_combo.addItem('HPS', 'hps')
        self.pitch_combo.addItem('自相关', 'autocorrelation')
        self.pitch_method = 'hps'
        self.pitch_combo.currentIndexChanged.connect(self.on_pitch_method_changed)

        param_layout.addWidget(fft_label, 0, 0)
        param_layout.addWidget(self.fft_combo, 0, 1)
        param_layout.addWidget(window_label, 1, 0)
        param_layout.addWidget(self.window_combo, 1, 1)
        param_layout.addWidget(peaks_label, 2, 0)
        param_layout.addWidget(self.peaks_combo, 2, 1)
        param_layout.addWidget(pitch_label, 3, 0)
        param_layout.addWidget(self.pitch_combo, 3, 1)

        layout.addLayout(param_layout)

        mode_layout = QVBoxLayout()
        mode_label = QLabel('当前模式:')
        self.mode_label = QLabel('实时分析')
        self.mode_label.setStyleSheet('color: #00ff88; font-weight: bold; font-size: 14px;')

        file_label = QLabel('当前文件:')
        self.file_label = QLabel('---')
        self.file_label.setStyleSheet('color: #00ccff; font-size: 11px;')

        selection_label = QLabel('选中区域:')
        self.selection_label = QLabel('---')
        self.selection_label.setStyleSheet('color: #ff9933; font-size: 11px;')

        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_label)
        mode_layout.addSpacing(10)
        mode_layout.addWidget(file_label)
        mode_layout.addWidget(self.file_label)
        mode_layout.addSpacing(10)
        mode_layout.addWidget(selection_label)
        mode_layout.addWidget(self.selection_label)

        layout.addLayout(mode_layout)
        panel.setLayout(layout)
        self.set_groupbox_style(panel)
        return panel

    def create_pitch_panel(self):
        panel = QGroupBox('基频与音符')
        layout = QHBoxLayout()
        layout.setSpacing(30)

        freq_layout = QVBoxLayout()
        freq_label = QLabel('基频 (Hz):')
        freq_label.setStyleSheet('color: white; font-size: 14px;')

        self.freq_value = QLabel('---')
        self.freq_value.setStyleSheet(
            'color: #00ff88; font-size: 36px; font-weight: bold; font-family: "Consolas", "Monospace";'
        )

        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_value)
        freq_layout.setAlignment(Qt.AlignCenter)

        note_layout = QVBoxLayout()
        note_label = QLabel('音符:')
        note_label.setStyleSheet('color: white; font-size: 14px;')

        self.note_value = QLabel('---')
        self.note_value.setStyleSheet(
            'color: #ffcc00; font-size: 36px; font-weight: bold; font-family: "Consolas", "Monospace";'
        )

        note_layout.addWidget(note_label)
        note_layout.addWidget(self.note_value)
        note_layout.setAlignment(Qt.AlignCenter)

        cents_layout = QVBoxLayout()
        cents_label = QLabel('音分偏差:')
        cents_label.setStyleSheet('color: white; font-size: 14px;')

        self.cents_value = QLabel('---')
        self.cents_value.setStyleSheet(
            'color: #ff6666; font-size: 24px; font-weight: bold; font-family: "Consolas", "Monospace";'
        )

        cents_layout.addWidget(cents_label)
        cents_layout.addWidget(self.cents_value)
        cents_layout.setAlignment(Qt.AlignCenter)

        peaks_info_layout = QVBoxLayout()
        peaks_title = QLabel('频谱峰值 (前5):')
        peaks_title.setStyleSheet('color: white; font-size: 14px;')

        self.peaks_info = QLabel('---')
        self.peaks_info.setStyleSheet(
            'color: #00ccff; font-size: 12px; font-family: "Consolas", "Monospace";'
        )

        peaks_info_layout.addWidget(peaks_title)
        peaks_info_layout.addWidget(self.peaks_info)
        peaks_info_layout.setAlignment(Qt.AlignLeft)

        layout.addLayout(freq_layout)
        layout.addLayout(note_layout)
        layout.addLayout(cents_layout)
        layout.addLayout(peaks_info_layout)
        layout.addStretch()

        panel.setLayout(layout)
        self.set_groupbox_style(panel)
        return panel

    def set_groupbox_style(self, groupbox):
        groupbox.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #333;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #88ccff;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QComboBox {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 4px;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #00ccff;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: white;
                selection-background-color: #006699;
            }
            QPushButton {
                background-color: #2a5a3a;
                color: white;
                border: 1px solid #4a8a5a;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7a4a;
                border-color: #6aba7a;
            }
            QPushButton:pressed {
                background-color: #1a3a2a;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
                border-color: #444444;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #2a2a2a;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ccff;
                border: 1px solid #0099cc;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)

    def apply_style(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(15, 15, 15))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f0f0f;
            }
            QWidget {
                background-color: #0f0f0f;
            }
        """)

    def on_fft_size_changed(self, index):
        self.fft_size = int(self.fft_combo.currentText())
        self.spectrum_analyzer.set_fft_size(self.fft_size)

    def on_window_changed(self, index):
        self.window_type = self.window_combo.currentData()
        self.spectrum_analyzer.set_window_type(self.window_type)

    def on_peaks_toggled(self, index):
        self.show_peaks = self.peaks_combo.currentData()
        if not self.show_peaks:
            self.spectrum_canvas.clear_peaks()
            self.peaks_info.setText('---')

    def on_pitch_method_changed(self, index):
        self.pitch_method = self.pitch_combo.currentData()

    def start_recording(self):
        self.mode = 'realtime'
        self.mode_label.setText('实时分析')
        self.waveform_canvas.set_duration(2.0)
        self.waveform_canvas.clear()
        self.spectrum_canvas.clear_peaks()
        self.pitch_buffer = np.zeros(4096, dtype=np.float32)

        self.audio_capture = AudioCapture(
            sample_rate=self.sample_rate,
            chunk=self.chunk,
            use_simulation=self.use_simulation
        )
        self.audio_capture.data_received.connect(self.on_audio_data)
        self.audio_capture.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_load.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.btn_analyze.setEnabled(False)

    def stop_recording(self):
        if self.audio_capture:
            self.audio_capture.stop()
            self.audio_capture = None

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_load.setEnabled(True)

    def on_audio_data(self, audio_data):
        self.waveform_canvas.update_realtime(audio_data)
        self.process_audio_frame(audio_data)

    def process_audio_frame(self, audio_data):
        freqs, magnitude_db = self.spectrum_analyzer.compute_spectrum(audio_data)

        peak_freqs = []
        peak_mags = []
        if self.show_peaks:
            peak_freqs, peak_mags = self.spectrum_analyzer.find_peaks(freqs, magnitude_db)

        self.spectrum_canvas.update_plot(freqs, magnitude_db, peak_freqs, peak_mags)

        n_samples = len(audio_data)
        if n_samples >= len(self.pitch_buffer):
            self.pitch_buffer = audio_data[-len(self.pitch_buffer):].copy()
        else:
            self.pitch_buffer = np.roll(self.pitch_buffer, -n_samples)
            self.pitch_buffer[-n_samples:] = audio_data

        pitch = self.pitch_detector.detect(self.pitch_buffer, method=self.pitch_method)

        if pitch > 0:
            self.freq_value.setText(f'{pitch:.1f}')
            note, half_steps = PitchDetector.frequency_to_note(pitch)
            self.note_value.setText(note)
            cents = PitchDetector.get_cents_deviation(pitch, half_steps)
            self.cents_value.setText(f'{cents:+d}')
        else:
            self.freq_value.setText('---')
            self.note_value.setText('---')
            self.cents_value.setText('---')

        if self.show_peaks and len(peak_freqs) > 0:
            peaks_text = ''
            for i, (freq, mag) in enumerate(zip(peak_freqs, peak_mags)):
                peaks_text += f'  P{i+1}: {freq:.0f}Hz ({mag:.0f}dB)\n'
            self.peaks_info.setText(peaks_text.strip())
        elif not self.show_peaks:
            self.peaks_info.setText('---')

    def load_wav_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择 WAV 文件', '', 'WAV Files (*.wav)'
        )
        if not file_path:
            return

        try:
            self.stop_recording()
            self.full_audio_data, sr = WavFileLoader.load_wav(file_path)
            self.sample_rate = sr
            self.selected_sample_rate = sr

            self.spectrum_analyzer.set_sample_rate(sr)
            self.pitch_detector.sample_rate = sr
            self.waveform_canvas.set_sample_rate(sr)

            self.waveform_canvas.plot_full_waveform(self.full_audio_data, sr)

            duration = len(self.full_audio_data) / sr
            self.mode = 'file'
            self.mode_label.setText('文件模式')
            self.file_label.setText(file_path.split('/')[-1])
            self.selection_label.setText('---')

            self.selected_audio_data = None
            self.btn_analyze.setEnabled(False)
            self.btn_play.setEnabled(False)

            QMessageBox.information(self, '加载成功',
                                   f'成功加载音频文件\n采样率: {sr} Hz\n时长: {duration:.2f} 秒')

        except Exception as e:
            QMessageBox.critical(self, '加载失败', f'无法加载文件: {str(e)}')

    def on_waveform_region_selected(self, start_time, end_time):
        if self.mode != 'file' or self.full_audio_data is None:
            return

        if end_time < start_time:
            start_time, end_time = end_time, start_time

        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)

        if end_sample > len(self.full_audio_data):
            end_sample = len(self.full_audio_data)

        if end_sample - start_sample < self.fft_size:
            QMessageBox.warning(self, '选择区域过小',
                               f'请选择至少 {self.fft_size / self.sample_rate:.3f} 秒的区域')
            return

        self.selected_audio_data = self.full_audio_data[start_sample:end_sample].copy()
        self.selection_label.setText(f'{start_time:.3f}s - {end_time:.3f}s')

        self.btn_analyze.setEnabled(True)
        self.btn_play.setEnabled(True)

    def on_spectrum_region_selected(self, freq_min, freq_max):
        if freq_max < freq_min:
            freq_min, freq_max = freq_max, freq_min
        self.statusBar().showMessage(f'频率范围: {freq_min:.0f}Hz - {freq_max:.0f}Hz', 3000)

        if self.mode != 'file' or self.full_audio_data is None:
            return

        if freq_max - freq_min < 10:
            return

        best_start, best_end = self._find_strongest_time_region(freq_min, freq_max)
        if best_start is not None and best_end is not None:
            start_sample = int(best_start * self.sample_rate)
            end_sample = int(best_end * self.sample_rate)
            if end_sample > len(self.full_audio_data):
                end_sample = len(self.full_audio_data)

            if end_sample - start_sample >= self.fft_size:
                self.selected_audio_data = self.full_audio_data[start_sample:end_sample].copy()
                self.selected_sample_rate = self.sample_rate
                self.selection_label.setText(f'{best_start:.3f}s - {best_end:.3f}s')
                self.waveform_canvas.highlight_region(best_start, best_end)
                self.btn_analyze.setEnabled(True)
                self.btn_play.setEnabled(True)

    def _find_strongest_time_region(self, freq_min, freq_max, window_duration=0.5, step=0.1):
        if self.full_audio_data is None or len(self.full_audio_data) == 0:
            return None, None

        total_duration = len(self.full_audio_data) / self.sample_rate
        if total_duration < window_duration:
            window_duration = total_duration
            step = window_duration / 2

        best_energy = -np.inf
        best_start = 0.0
        best_end = window_duration

        t = 0.0
        while t + window_duration <= total_duration:
            start_sample = int(t * self.sample_rate)
            end_sample = start_sample + int(window_duration * self.sample_rate)
            segment = self.full_audio_data[start_sample:end_sample]

            if len(segment) < self.fft_size:
                padded = np.zeros(self.fft_size)
                padded[:len(segment)] = segment
                segment = padded

            window = np.hanning(len(segment))
            segment_windowed = segment * window
            fft_result = np.fft.rfft(segment_windowed, self.fft_size)
            magnitude = np.abs(fft_result)
            freqs = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)

            freq_mask = (freqs >= freq_min) & (freqs <= freq_max)
            if np.any(freq_mask):
                energy = np.mean(magnitude[freq_mask] ** 2)
                if energy > best_energy:
                    best_energy = energy
                    best_start = t
                    best_end = t + window_duration

            t += step

        return best_start, best_end

    def analyze_selection(self):
        if self.selected_audio_data is None:
            return

        freqs, magnitude_db = self.spectrum_analyzer.compute_spectrum(self.selected_audio_data)

        peak_freqs = []
        peak_mags = []
        if self.show_peaks:
            peak_freqs, peak_mags = self.spectrum_analyzer.find_peaks(freqs, magnitude_db)

        self.spectrum_canvas.update_plot(freqs, magnitude_db, peak_freqs, peak_mags)

        pitch = self.pitch_detector.detect(self.selected_audio_data, method=self.pitch_method)

        if pitch > 0:
            self.freq_value.setText(f'{pitch:.1f}')
            note, half_steps = PitchDetector.frequency_to_note(pitch)
            self.note_value.setText(note)
            cents = PitchDetector.get_cents_deviation(pitch, half_steps)
            self.cents_value.setText(f'{cents:+d}')
        else:
            self.freq_value.setText('---')
            self.note_value.setText('---')
            self.cents_value.setText('---')

        if self.show_peaks and len(peak_freqs) > 0:
            peaks_text = ''
            for i, (freq, mag) in enumerate(zip(peak_freqs, peak_mags)):
                peaks_text += f'  P{i+1}: {freq:.0f}Hz ({mag:.0f}dB)\n'
            self.peaks_info.setText(peaks_text.strip())

    def play_selection(self):
        if self.selected_audio_data is None or self.selected_sample_rate is None:
            return

        if self.audio_player and self.audio_player.isRunning():
            self.audio_player.stop()

        self.audio_player = AudioPlayer(self.selected_audio_data, self.selected_sample_rate)
        self.audio_player.playback_finished.connect(self.on_playback_finished)
        self.audio_player.start()
        self.btn_play.setEnabled(False)

    def on_playback_finished(self):
        self.btn_play.setEnabled(True)

    def closeEvent(self, event):
        self.stop_recording()
        if self.audio_player:
            self.audio_player.stop()
        event.accept()


def main():
    matplotlib.rcParams['figure.dpi'] = 120
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    font = app.font()
    font.setPointSize(font.pointSize() + 1)
    app.setFont(font)

    window = AudioSpectrumAnalyzer()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
