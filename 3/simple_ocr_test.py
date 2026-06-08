import cv2
import easyocr

print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False)
print("EasyOCR initialized!")

img = cv2.imread('test_plate_cropped.jpg')
print(f"\nImage shape: {img.shape}")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

cv2.imwrite('ocr_test_input.jpg', binary)
print("Saved test input to ocr_test_input.jpg")

print("\n" + "="*50)
print("Testing OCR on binary image...")
results = reader.readtext(binary, detail=1, paragraph=False)
print(f"Found {len(results)} results:")
for i, (bbox, text, conf) in enumerate(results):
    print(f"  {i+1}. '{text}' (confidence: {conf:.4f})")

print("\n" + "="*50)
print("Testing OCR on original color image...")
results2 = reader.readtext(img, detail=1, paragraph=False)
print(f"Found {len(results2)} results:")
for i, (bbox, text, conf) in enumerate(results2):
    print(f"  {i+1}. '{text}' (confidence: {conf:.4f})")

print("\n" + "="*50)
print("Testing OCR on grayscale image...")
results3 = reader.readtext(gray, detail=1, paragraph=False)
print(f"Found {len(results3)} results:")
for i, (bbox, text, conf) in enumerate(results3):
    print(f"  {i+1}. '{text}' (confidence: {conf:.4f})")

print("\nDone!")
