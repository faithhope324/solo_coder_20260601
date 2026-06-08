print("Testing imports...")
try:
    from plate_detector import PlateDetector
    print("✓ PlateDetector imported")
except Exception as e:
    print(f"✗ PlateDetector error: {e}")

try:
    from ocr_recognizer import OCRRecognizer
    print("✓ OCRRecognizer imported")
except Exception as e:
    print(f"✗ OCRRecognizer error: {e}")

print("Import test completed!")
