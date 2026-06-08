import urllib.request
import json

print("Testing API recognition...")

try:
    with open('test_plate.jpg', 'rb') as f:
        image_data = f.read()
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="image"; filename="test_plate.jpg"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'
    ).encode('utf-8') + image_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }
    
    req = urllib.request.Request(
        'http://127.0.0.1:5000/api/recognize',
        data=body,
        headers=headers,
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=60) as r:
        response = json.loads(r.read().decode('utf-8'))
        print(f"Status: {r.status}")
        print(f"Success: {response.get('success')}")
        print(f"Plate: {response.get('plate_number')}")
        print(f"Confidence: {response.get('confidence')}%")
        print(f"Result image: {response.get('result_image')}")
        print("\n✓ API test completed!")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
