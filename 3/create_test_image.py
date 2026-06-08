import cv2
import numpy as np

img = np.ones((500, 800, 3), dtype=np.uint8) * 220

cv2.rectangle(img, (100, 180), (700, 320), (255, 255, 255), -1)
cv2.rectangle(img, (100, 180), (700, 320), (0, 0, 255), 4)

small_rect = img[180:320, 100:180].copy()
cv2.rectangle(small_rect, (0, 0), (80, 140), (0, 0, 255), -1)
cv2.putText(small_rect, 'JING', (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4)
img[180:320, 100:180] = small_rect

cv2.putText(img, 'A12345', (220, 285), cv2.FONT_HERSHEY_SIMPLEX, 3.8, (0, 0, 0), 8)

cv2.imwrite('test_plate.jpg', img)
print('Test image created: test_plate.jpg')

import os
print(f'File size: {os.path.getsize("test_plate.jpg")} bytes')
print(f'Image shape: {img.shape}')

cv2.imwrite('test_plate_cropped.jpg', img[180:320, 100:700])
print('Cropped plate saved: test_plate_cropped.jpg')
