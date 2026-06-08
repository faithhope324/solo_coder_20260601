import urllib.request

print("Testing server...")
try:
    r = urllib.request.urlopen('http://127.0.0.1:5000')
    print(f"Status: {r.status}")
    print(f"Content-Type: {r.headers.get('Content-Type')}")
    content = r.read()
    print(f"Content length: {len(content)} bytes")
    print("✓ Homepage loads successfully")
except Exception as e:
    print(f"✗ Error: {e}")
