import numpy as np
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import pyqtSignal
from matplotlib.widgets import SpanSelector


class WaveformCanvas(FigureCanvas):
    region_selected = pyqtSignal(float, float)

    def __init__(self, parent=None, width=8, height=2.5, dpi=120, duration=2.0, sample_rate=44100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        self.duration = duration
        self.sample_rate = sample_rate
        self.max_samples = int(duration * sample_rate)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#0a0a0a')
        self.fig.patch.set_facecolor('#0a0a0a')

        self.line, = self.ax.plot([], [], color='#00ccff', linewidth=0.8)
        self.center_line = self.ax.axhline(y=0, color='#444444', linestyle='-', alpha=0.5)

        self.ax.set_xlabel('时间 (s)', color='white', fontsize=9)
        self.ax.set_ylabel('振幅', color='white', fontsize=9)
        self.ax.set_ylim(-1.0, 1.0)
        self.ax.grid(True, alpha=0.2, color='gray')
        self.ax.tick_params(axis='x', colors='white', labelsize=8)
        self.ax.tick_params(axis='y', colors='white', labelsize=8)

        self.span = None
        self.selection_patch = None
        self.selection_start = None
        self.selection_end = None

        self.buffer = np.zeros(self.max_samples, dtype=np.float32)
        self.time_axis = np.linspace(0, duration, self.max_samples)

        self._update_xlim()
        self.fig.tight_layout()

    def _update_xlim(self):
        if self.sample_rate > 0:
            self.max_samples = int(self.duration * self.sample_rate)
            self.time_axis = np.linspace(0, self.duration, self.max_samples)
            self.ax.set_xlim(0, self.duration)

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
        self._update_xlim()

    def set_duration(self, duration):
        self.duration = duration
        self._update_xlim()

    def update_realtime(self, audio_data):
        n_samples = len(audio_data)

        if n_samples >= self.max_samples:
            self.buffer = audio_data[-self.max_samples:].copy()
        else:
            self.buffer = np.roll(self.buffer, -n_samples)
            self.buffer[-n_samples:] = audio_data

        self.line.set_data(self.time_axis, self.buffer)
        self.draw_idle()

    def plot_full_waveform(self, audio_data, sample_rate=None):
        if sample_rate:
            self.sample_rate = sample_rate

        n_samples = len(audio_data)
        duration = n_samples / self.sample_rate

        self.time_axis = np.linspace(0, duration, n_samples)
        self.ax.set_xlim(0, duration)
        self.ax.set_xlabel('时间 (s)', color='white', fontsize=9)

        self.line.set_data(self.time_axis, audio_data)

        if self.span is None:
            self.span = SpanSelector(
                self.ax,
                self.on_select,
                "horizontal",
                useblit=True,
                props=dict(alpha=0.3, facecolor="#ff6600"),
                interactive=True,
                drag_from_anywhere=True
            )

        self.selection_start = None
        self.selection_end = None

        self.draw_idle()

    def on_select(self, xmin, xmax):
        self.selection_start = xmin
        self.selection_end = xmax
        self.region_selected.emit(xmin, xmax)

    def get_selection(self):
        if self.selection_start is None or self.selection_end is None:
            return None
        return min(self.selection_start, self.selection_end), max(self.selection_start, self.selection_end)

    def clear(self):
        self.buffer = np.zeros(self.max_samples, dtype=np.float32)
        self.line.set_data([], [])
        self.selection_start = None
        self.selection_end = None
        if self.span:
            self.span.extents = (0, 0)
        self.draw_idle()

    def highlight_region(self, start_time, end_time):
        if self.selection_patch:
            self.selection_patch.remove()

        y_min, y_max = self.ax.get_ylim()
        self.selection_patch = self.ax.axvspan(
            start_time, end_time,
            facecolor='#ff6600',
            alpha=0.3,
            edgecolor='#ff9933',
            linewidth=1
        )
        self.draw_idle()

    def clear_highlight(self):
        if self.selection_patch:
            self.selection_patch.remove()
            self.selection_patch = None
            self.draw_idle()
