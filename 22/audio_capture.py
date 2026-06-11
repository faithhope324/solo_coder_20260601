import numpy as np
import wave
from PyQt5.QtCore import QThread, pyqtSignal
import time

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None


class AudioCapture(QThread):
    data_received = pyqtSignal(np.ndarray)

    def __init__(self, sample_rate=44100, chunk=1024, channels=1, use_simulation=False):
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.channels = channels
        self.is_running = False
        self.audio = None
        self.stream = None
        self.use_simulation = use_simulation
        self._time = 0.0

    def _generate_simulated_audio(self):
        t = np.arange(self._time, self._time + self.chunk / self.sample_rate, 1/self.sample_rate)
        freq1 = 440 + 50 * np.sin(2 * np.pi * 0.5 * self._time)
        freq2 = 880 + 30 * np.sin(2 * np.pi * 0.3 * self._time)
        noise = np.random.normal(0, 0.05, len(t))
        audio = 0.3 * np.sin(2 * np.pi * freq1 * t) + 0.15 * np.sin(2 * np.pi * freq2 * t) + noise
        self._time += self.chunk / self.sample_rate
        return audio.astype(np.float32)

    def run(self):
        self.is_running = True

        if self.use_simulation or (not PYAUDIO_AVAILABLE and not SOUNDDEVICE_AVAILABLE):
            self._run_simulation()
        elif PYAUDIO_AVAILABLE:
            self._run_pyaudio()
        else:
            self._run_sounddevice()

    def _run_simulation(self):
        while self.is_running:
            try:
                audio_data = self._generate_simulated_audio()
                self.data_received.emit(audio_data)
                time.sleep(self.chunk / self.sample_rate)
            except Exception as e:
                print(f"Simulation error: {e}")
                break

    def _run_pyaudio(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        while self.is_running:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                if self.channels > 1:
                    expected_len = self.chunk * self.channels
                    actual_len = len(audio_data)
                    if actual_len >= expected_len:
                        audio_data = audio_data[:expected_len].reshape(-1, self.channels).mean(axis=1)
                    else:
                        n_frames = actual_len // self.channels
                        if n_frames > 0:
                            audio_data = audio_data[:n_frames * self.channels].reshape(-1, self.channels).mean(axis=1)
                        else:
                            audio_data = audio_data[:self.channels].mean()
                            audio_data = np.array([audio_data], dtype=np.float32)
                self.data_received.emit(audio_data)
            except Exception as e:
                print(f"Audio capture error: {e}")
                break

    def _run_sounddevice(self):
        def callback(indata, frames, time, status):
            if status:
                print(status)
            audio_data = indata[:, 0] if indata.shape[1] > 1 else indata.flatten()
            self.data_received.emit(audio_data.astype(np.float32))

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.chunk,
            channels=self.channels,
            dtype='float32',
            callback=callback
        )
        self.stream.start()

        while self.is_running:
            time.sleep(0.01)

    def stop(self):
        self.is_running = False
        if self.stream:
            if PYAUDIO_AVAILABLE and hasattr(self.stream, 'stop_stream'):
                self.stream.stop_stream()
                self.stream.close()
            elif SOUNDDEVICE_AVAILABLE and hasattr(self.stream, 'stop'):
                self.stream.stop()
                self.stream.close()
        if self.audio:
            self.audio.terminate()
        self.wait()


class WavFileLoader:
    @staticmethod
    def load_wav(file_path):
        with wave.open(file_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        if sample_width == 1:
            dtype = np.uint8
            max_val = 128.0
        elif sample_width == 2:
            dtype = np.int16
            max_val = 32768.0
        elif sample_width == 4:
            dtype = np.int32
            max_val = 2147483648.0
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")

        audio_data = np.frombuffer(raw_data, dtype=dtype).astype(np.float32) / max_val

        if channels > 1:
            expected_len = n_frames * channels
            actual_len = len(audio_data)
            usable_frames = min(n_frames, actual_len // channels)
            if usable_frames > 0:
                audio_data = audio_data[:usable_frames * channels].reshape(-1, channels).mean(axis=1)
            else:
                audio_data = np.zeros(n_frames, dtype=np.float32)

        return audio_data, sample_rate

    @staticmethod
    def save_wav(file_path, audio_data, sample_rate):
        audio_int = (audio_data * 32767).astype(np.int16)
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int.tobytes())


class AudioPlayer(QThread):
    playback_finished = pyqtSignal()

    def __init__(self, audio_data, sample_rate):
        super().__init__()
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.is_running = False

    def run(self):
        self.is_running = True

        if PYAUDIO_AVAILABLE:
            self._play_with_pyaudio()
        elif SOUNDDEVICE_AVAILABLE:
            self._play_with_sounddevice()
        else:
            print("No audio playback library available. Install pyaudio or sounddevice.")
            self.playback_finished.emit()

        self.is_running = False

    def _play_with_pyaudio(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            output=True
        )

        audio_bytes = self.audio_data.astype(np.float32).tobytes()
        stream.write(audio_bytes)

        stream.stop_stream()
        stream.close()
        audio.terminate()
        self.playback_finished.emit()

    def _play_with_sounddevice(self):
        sd.play(self.audio_data, self.sample_rate)
        sd.wait()
        self.playback_finished.emit()

    def stop(self):
        self.is_running = False
        if SOUNDDEVICE_AVAILABLE:
            sd.stop()
        self.wait()
