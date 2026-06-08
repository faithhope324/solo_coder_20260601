import cv2
import numpy as np
from typing import List, Tuple, Optional


class PlateDetector:
    def __init__(self):
        self.min_area = 500
        self.max_area = 200000
        self.min_ratio = 1.5
        self.max_ratio = 6.0

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return blurred

    def binarize(self, image: np.ndarray) -> np.ndarray:
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        edges = cv2.Canny(image, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        return edges

    def find_contours(self, edges: np.ndarray) -> List[np.ndarray]:
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    def is_plate_like(self, contour: np.ndarray) -> bool:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        ratio = float(w) / h if h > 0 else 0
        
        if area < self.min_area or area > self.max_area:
            return False
        if ratio < self.min_ratio or ratio > self.max_ratio:
            return False
        return True

    def perspective_transform(self, image: np.ndarray, contour: np.ndarray) -> Optional[np.ndarray]:
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        
        width = int(rect[1][0])
        height = int(rect[1][1])
        
        if width < height:
            width, height = height, width
        
        src_pts = box.astype("float32")
        dst_pts = np.array([[0, height-1],
                           [0, 0],
                           [width-1, 0],
                           [width-1, height-1]], dtype="float32")
        
        try:
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(image, M, (width, height))
            return warped
        except:
            return None

    def detect_plate(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[List], Optional[np.ndarray]]:
        image = cv2.imread(image_path)
        if image is None:
            return None, None, None
        
        preprocessed = self.preprocess(image)
        edges = self.detect_edges(preprocessed)
        contours = self.find_contours(edges)
        
        for contour in contours:
            if self.is_plate_like(contour):
                x, y, w, h = cv2.boundingRect(contour)
                plate_region = image[y:y+h, x:x+w]
                
                warped = self.perspective_transform(image, contour)
                if warped is not None:
                    plate_region = warped
                
                plate_box = [x, y, w, h]
                return plate_region, plate_box, image
        
        return None, None, image

    def draw_plate_box(self, image: np.ndarray, plate_box: List, text: str = "") -> np.ndarray:
        if plate_box is None:
            return image
        
        x, y, w, h = plate_box
        result = image.copy()
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        if text:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            thickness = 2
            text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
            
            cv2.rectangle(result, (x, y - text_size[1] - 10), 
                         (x + text_size[0], y), (0, 255, 0), -1)
            cv2.putText(result, text, (x, y - 5), font, font_scale, (0, 0, 0), thickness)
        
        return result
