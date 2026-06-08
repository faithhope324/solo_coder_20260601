import cv2
import numpy as np
from ocr_recognizer import OCRRecognizer

print("=" * 60)
print("Debug OCR Recognition")
print("=" * 60)

recognizer = OCRRecognizer()

img = cv2.imread('test_plate.jpg')
print(f"\nOriginal image shape: {img.shape}")

plate_region = img[150:250, 100:500]
print(f"Plate region shape: {plate_region.shape}")

cv2.imwrite('debug_plate_region.jpg', plate_region)
print("Saved plate region to debug_plate_region.jpg")

preprocessed = recognizer.preprocess_plate(plate_region)
print(f"Preprocessed shape: {preprocessed.shape}")
cv2.imwrite('debug_preprocessed.jpg', preprocessed)
print("Saved preprocessed image to debug_preprocessed.jpg")

preprocessed_v2 = recognizer.preprocess_plate_v2(plate_region)
cv2.imwrite('debug_preprocessed_v2.jpg', preprocessed_v2)
print("Saved preprocessed_v2 image to debug_preprocessed_v2.jpg")

print("\n" + "=" * 60)
print("Testing OCR on original plate region:")
results1 = recognizer.reader.readtext(plate_region, detail=1, paragraph=False)
print(f"Results: {len(results1)} items")
for i, (bbox, text, conf) in enumerate(results1):
    print(f"  {i+1}. Text: '{text}', Confidence: {conf:.4f}")

print("\n" + "=" * 60)
print("Testing OCR on preprocessed image:")
results2 = recognizer.reader.readtext(preprocessed, detail=1, paragraph=False)
print(f"Results: {len(results2)} items")
for i, (bbox, text, conf) in enumerate(results2):
    print(f"  {i+1}. Text: '{text}', Confidence: {conf:.4f}")

print("\n" + "=" * 60)
print("Testing OCR on preprocessed_v2 image:")
results3 = recognizer.reader.readtext(preprocessed_v2, detail=1, paragraph=False)
print(f"Results: {len(results3)} items")
for i, (bbox, text, conf) in enumerate(results3):
    print(f"  {i+1}. Text: '{text}', Confidence: {conf:.4f}")

print("\n" + "=" * 60)
print("Testing OCR with allowlist:")
allowed = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
results4 = recognizer.reader.readtext(preprocessed, detail=1, paragraph=False, allowlist=allowed)
print(f"Results: {len(results4)} items")
for i, (bbox, text, conf) in enumerate(results4):
    print(f"  {i+1}. Text: '{text}', Confidence: {conf:.4f}")

print("\n" + "=" * 60)
print("Final recognize() method result:")
plate_text, confidence = recognizer.recognize(plate_region)
print(f"Plate: '{plate_text}', Confidence: {confidence:.4f}")

print("\n" + "=" * 60)
print("Debug completed!")
