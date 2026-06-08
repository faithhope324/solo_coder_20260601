import easyocr
import cv2
import numpy as np
from typing import Tuple, Optional


class OCRRecognizer:
    def __init__(self, languages: list = ['ch_sim', 'en']):
        self.reader = easyocr.Reader(languages, gpu=False)
        self.allowed_chars = set('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领警学')

    def preprocess_plate(self, plate_image: np.ndarray) -> np.ndarray:
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image
        
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return binary

    def preprocess_plate_v2(self, plate_image: np.ndarray) -> np.ndarray:
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image
        
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        return binary

    def filter_text(self, text: str) -> str:
        text = text.upper().strip()
        text = text.replace(' ', '').replace('·', '').replace('-', '')
        text = text.replace('O', '0').replace('I', '1').replace('L', '1')
        filtered = ''.join([c for c in text if c in self.allowed_chars])
        return filtered

    def recognize(self, plate_image: np.ndarray) -> Tuple[str, float]:
        if plate_image is None:
            return "", 0.0
        
        try:
            preprocessed = self.preprocess_plate(plate_image)
            
            results = self.reader.readtext(
                preprocessed,
                detail=1,
                paragraph=False
            )
            
            if not results:
                preprocessed_v2 = self.preprocess_plate_v2(plate_image)
                results = self.reader.readtext(preprocessed_v2, detail=1, paragraph=False)
            
            if not results:
                results = self.reader.readtext(plate_image, detail=1, paragraph=False)
            
            if results:
                full_text = ""
                total_confidence = 0.0
                count = 0
                
                for bbox, text, confidence in results:
                    filtered_text = self.filter_text(text)
                    if filtered_text:
                        full_text += filtered_text
                        total_confidence += confidence
                        count += 1
                
                if count > 0:
                    avg_confidence = total_confidence / count
                    return full_text[:10], avg_confidence
            
            return "", 0.0
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return "", 0.0

    def recognize_from_path(self, image_path: str) -> Tuple[str, float]:
        image = cv2.imread(image_path)
        if image is None:
            return "", 0.0
        return self.recognize(image)
