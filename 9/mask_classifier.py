import cv2
import numpy as np
import os


class MaskClassifier:
    INPUT_SIZE = (224, 224)

    def __init__(self, model_path=None):
        self.model = None
        self.use_cnn = False

        if model_path and os.path.exists(model_path):
            self._load_model(model_path)

    def _load_model(self, model_path):
        try:
            from tensorflow.keras.models import load_model

            self.model = load_model(model_path)
            self.use_cnn = True
            print(f"[MaskClassifier] CNN model loaded: {model_path}")
        except ImportError:
            print("[MaskClassifier] TensorFlow not installed, using heuristic")
            self.use_cnn = False
        except Exception as e:
            print(f"[MaskClassifier] Model load failed: {e}")
            self.use_cnn = False

    def predict(self, face_roi):
        if face_roi is None or face_roi.size == 0:
            return False, 0.0

        if self.use_cnn and self.model is not None:
            return self._predict_cnn(face_roi)
        return self._predict_heuristic(face_roi)

    def _predict_cnn(self, face_roi):
        try:
            resized = cv2.resize(face_roi, self.INPUT_SIZE)
            arr = resized.astype(np.float32) / 255.0
            arr = np.expand_dims(arr, axis=0)
            pred = self.model.predict(arr, verbose=0)[0][0]
            has_mask = bool(pred > 0.5)
            confidence = float(pred) if has_mask else float(1.0 - pred)
            return has_mask, confidence
        except Exception:
            return self._predict_heuristic(face_roi)

    def _predict_heuristic(self, face_roi):
        h, w = face_roi.shape[:2]
        lower = face_roi[int(h * 0.55) :, :]
        if lower.size == 0:
            return False, 0.5

        hsv = cv2.cvtColor(lower, cv2.COLOR_BGR2HSV)

        skin1 = cv2.inRange(hsv, np.array([0, 30, 60]), np.array([25, 180, 255]))
        skin2 = cv2.inRange(hsv, np.array([160, 30, 60]), np.array([180, 180, 255]))
        skin_mask = cv2.bitwise_or(skin1, skin2)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)

        total_px = lower.shape[0] * lower.shape[1]
        skin_px = cv2.countNonZero(skin_mask)
        skin_ratio = skin_px / total_px if total_px > 0 else 0

        blue_mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
        white_mask = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 50, 255]))
        mask_px = cv2.countNonZero(blue_mask) + cv2.countNonZero(white_mask)
        mask_ratio = mask_px / total_px if total_px > 0 else 0

        has_mask = skin_ratio < 0.30 or (mask_ratio > 0.3 and skin_ratio < 0.5)

        if has_mask:
            confidence = min(0.92, 0.6 + mask_ratio * 0.5)
        else:
            confidence = min(0.90, 0.5 + skin_ratio * 0.6)

        return has_mask, confidence
