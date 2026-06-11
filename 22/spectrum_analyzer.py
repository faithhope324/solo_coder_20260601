import numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import pyqtSignal
from matplotlib.widgets import SpanSelector


class SpectrumAnalyzer:
    def __init__(self, sample_rate=44100, fft_size=1024, window_type='hann', max_freq=8000):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.window_type = window_type
        self.max_freq = max_freq
        self.window = self._get_window()

    def _get_window(self):
        if self.window_type == 'hann':
            return np.hanning(self.fft_size)
        elif self.window_type == 'hamming':
            return np.hamming(self.fft_size)
        elif self.window_type == 'rect':
            return np.ones(self.fft_size)
        else:
            return np.hanning(self.fft_size)

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size
        self.window = self._get_window()

    def set_window_type(self, window_type):
        self.window_type = window_type
        self.window = self._get_window()

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate

    def compute_spectrum(self, audio_data):
        if len(audio_data) < self.fft_size:
            padded = np.zeros(self.fft_size)
            padded[:len(audio_data)] = audio_data
            audio_data = padded

        audio_segment = audio_data[:self.fft_size]
        audio_segment = audio_segment - np.mean(audio_segment)
        windowed = audio_segment * self.window

        fft_result = np.fft.rfft(windowed, self.fft_size)
        magnitude = np.abs(fft_result)

        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)

        max_idx = int(self.max_freq * self.fft_size / self.sample_rate)
        max_idx = min(max_idx, len(magnitude) - 1)

        freqs = freqs[:max_idx]
        magnitude = magnitude[:max_idx]

        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        magnitude_db = magnitude_db - np.max(magnitude_db)

        return freqs, magnitude_db

    def find_peaks(self, freqs, magnitude_db, n_peaks=5, min_height=-60, min_distance=5):
        peaks, properties = find_peaks(
            magnitude_db,
            height=min_height,
            distance=min_distance,
            prominence=3
        )

        if len(peaks) == 0:
            return [], []

        peak_magnitudes = magnitude_db[peaks]
        peak_freqs = freqs[peaks]

        sorted_indices = np.argsort(peak_magnitudes)[::-1]
        top_indices = sorted_indices[:n_peaks]

        return peak_freqs[top_indices], peak_magnitudes[top_indices]


class SpectrumCanvas(FigureCanvas):
    region_selected = pyqtSignal(float, float)

    def __init__(self, parent=None, width=8, height=3, dpi=120):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#0a0a0a')
        self.fig.patch.set_facecolor('#0a0a0a')

        self.line, = self.ax.plot([], [], color='#00ff88', linewidth=1.5)
        self.peak_lines = []
        self.peak_annotations = []

        self.ax.set_xlabel('频率 (Hz)', color='white', fontsize=9)
        self.ax.set_ylabel('幅度 (dB)', color='white', fontsize=9)
        self.ax.set_xlim(0, 8000)
        self.ax.set_ylim(-100, 5)
        self.ax.grid(True, alpha=0.2, color='gray')
        self.ax.tick_params(axis='x', colors='white', labelsize=8)
        self.ax.tick_params(axis='y', colors='white', labelsize=8)

        self.span = SpanSelector(
            self.ax,
            self.on_select,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.3, facecolor="#ff6600"),
            interactive=True,
            drag_from_anywhere=True
        )

        self.fig.tight_layout()

    def on_select(self, xmin, xmax):
        self.region_selected.emit(xmin, xmax)

    def update_plot(self, freqs, magnitude_db, peak_freqs=None, peak_mags=None):
        self.line.set_data(freqs, magnitude_db)

        for line in self.peak_lines:
            line.remove()
        self.peak_lines = []

        for ann in self.peak_annotations:
            ann.remove()
        self.peak_annotations = []

        if peak_freqs is not None and len(peak_freqs) > 0:
            colors = ['#ff0066', '#ff6600', '#ffcc00', '#00ccff', '#cc66ff']
            for i, (freq, mag) in enumerate(zip(peak_freqs, peak_mags)):
                color = colors[i % len(colors)]
                line = self.ax.axvline(x=freq, color=color, linestyle='--', alpha=0.7, linewidth=1)
                self.peak_lines.append(line)
                ann = self.ax.annotate(
                    f'{freq:.0f}Hz',
                    xy=(freq, mag),
                    xytext=(5, 5),
                    textcoords='offset points',
                    color=color,
                    fontsize=8,
                    fontweight='bold'
                )
                self.peak_annotations.append(ann)

        self.draw_idle()

    def clear_peaks(self):
        for line in self.peak_lines:
            line.remove()
        self.peak_lines = []
        for ann in self.peak_annotations:
            ann.remove()
        self.peak_annotations = []
        self.draw_idle()
