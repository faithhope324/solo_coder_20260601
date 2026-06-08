import cv2
import numpy as np


class FaceDetector:
    def __init__(self, scale_factor=1.1, min_neighbors=5, min_size=(100, 100)):
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size

        self.frontal_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.profile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_profileface.xml"
        )

        if self.frontal_cascade.empty():
            raise RuntimeError("Failed to load haarcascade_frontalface_default.xml")
        if self.profile_cascade.empty():
            raise RuntimeError("Failed to load haarcascade_profileface.xml")

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.frontal_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size,
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        if len(faces) == 0:
            faces = self.profile_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_size,
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

        return faces

    @staticmethod
    def annotate_frame(frame, faces, mask_results):
        for i, (x, y, w, h) in enumerate(faces):
            has_mask = mask_results[i]["has_mask"]
            confidence = mask_results[i]["confidence"]

            if has_mask:
                color = (0, 255, 0)
                label = f"Mask {confidence:.1%}"
            else:
                color = (0, 0, 255)
                label = f"No Mask {confidence:.1%}"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x, y - th - 10), (x + tw, y), color, -1)
            cv2.putText(
                frame,
                label,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

        return frame
