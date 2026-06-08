import cv2
import time
import threading
from face_detector import FaceDetector
from mask_classifier import MaskClassifier


class CameraStream:
    def __init__(self, camera_index=0, model_path=None):
        self.camera_index = camera_index
        self.face_detector = FaceDetector()
        self.mask_classifier = MaskClassifier(model_path=model_path)
        self.camera = None
        self.is_running = False
        self._lock = threading.Lock()
        self._frame_count = 0
        self._fps = 0.0
        self._fps_time = time.time()

    def start(self):
        self.camera = cv2.VideoCapture(self.camera_index)
        if not self.camera.isOpened():
            raise RuntimeError(f"Cannot open camera index {self.camera_index}")
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        self.is_running = True
        self._fps_time = time.time()
        self._frame_count = 0

    def stop(self):
        self.is_running = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def process_frame(self, frame):
        faces = self.face_detector.detect(frame)
        results = []

        for x, y, w, h in faces:
            roi = frame[y : y + h, x : x + w]
            has_mask, confidence = self.mask_classifier.predict(roi)
            results.append(
                {
                    "box": (int(x), int(y), int(w), int(h)),
                    "has_mask": bool(has_mask),
                    "confidence": float(confidence),
                }
            )

        annotated = FaceDetector.annotate_frame(frame, faces, results)
        return annotated, results

    def _update_fps(self):
        self._frame_count += 1
        elapsed = time.time() - self._fps_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_time = time.time()

    def generate_frames(self):
        while self.is_running:
            success, frame = self.camera.read()
            if not success:
                time.sleep(0.03)
                continue

            with self._lock:
                processed, _ = self.process_frame(frame)

            self._update_fps()

            cv2.putText(
                processed,
                f"FPS: {self._fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
            )

            ret, buf = cv2.imencode(
                ".jpg", processed, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
            )

    def capture_single(self):
        if self.camera is None or not self.camera.isOpened():
            return None, []
        success, frame = self.camera.read()
        if not success:
            return None, []
        processed, results = self.process_frame(frame)
        return processed, results
