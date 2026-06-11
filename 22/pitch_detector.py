import numpy as np
from scipy.signal import find_peaks


NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


class PitchDetector:
    def __init__(self, sample_rate=44100, min_freq=50, max_freq=4000):
        self.sample_rate = sample_rate
        self.min_freq = min_freq
        self.max_freq = max_freq

    def detect_autocorrelation(self, audio_data):
        if len(audio_data) < 2:
            return 0.0

        audio_data = audio_data - np.mean(audio_data)

        min_lag = int(self.sample_rate / self.max_freq)
        max_lag = int(self.sample_rate / self.min_freq)
        max_lag = min(max_lag, len(audio_data) // 2)
        min_lag = max(min_lag, 1)

        corr = np.correlate(audio_data, audio_data, mode='full')
        corr = corr[len(corr) // 2:]

        if len(corr) < max_lag + 1:
            return 0.0

        peaks, properties = find_peaks(corr[min_lag:max_lag], height=0)
        if len(peaks) == 0:
            return 0.0

        peaks += min_lag
        max_peak_idx = np.argmax(corr[peaks])
        best_lag = peaks[max_peak_idx]

        if best_lag > 0:
            return self.sample_rate / best_lag
        return 0.0

    def detect_hps(self, audio_data, n_harmonics=4):
        if len(audio_data) < 2:
            return 0.0

        audio_data = audio_data - np.mean(audio_data)

        window = np.hanning(len(audio_data))
        audio_windowed = audio_data * window

        fft_size = len(audio_data)
        spectrum = np.abs(np.fft.rfft(audio_windowed, fft_size))
        freqs = np.fft.rfftfreq(fft_size, 1.0 / self.sample_rate)

        hps_spectrum = np.copy(spectrum)
        for h in range(2, n_harmonics + 1):
            downsampled = spectrum[::h]
            hps_spectrum[:len(downsampled)] *= downsampled

        min_idx = int(self.min_freq * fft_size / self.sample_rate)
        max_idx = int(self.max_freq * fft_size / self.sample_rate)
        max_idx = min(max_idx, len(hps_spectrum) - 1)
        min_idx = max(min_idx, 1)

        if min_idx >= max_idx:
            return 0.0

        peak_idx = np.argmax(hps_spectrum[min_idx:max_idx]) + min_idx
        return freqs[peak_idx]

    def detect(self, audio_data, method='hps'):
        if method == 'autocorrelation':
            return self.detect_autocorrelation(audio_data)
        else:
            return self.detect_hps(audio_data)

    @staticmethod
    def frequency_to_note(frequency):
        if frequency <= 0:
            return "---", 0

        A4 = 440.0
        C0 = A4 * np.power(2, -4.75)

        half_steps = int(round(12 * np.log2(frequency / C0)))
        octave = half_steps // 12
        note_index = half_steps % 12

        note_name = NOTE_NAMES[note_index]
        return f"{note_name}{octave}", half_steps

    @staticmethod
    def get_cents_deviation(frequency, half_steps):
        if frequency <= 0:
            return 0

        A4 = 440.0
        C0 = A4 * np.power(2, -4.75)
        exact_freq = C0 * np.power(2, half_steps / 12)

        if exact_freq <= 0:
            return 0

        cents = 1200 * np.log2(frequency / exact_freq)
        return int(round(cents))
