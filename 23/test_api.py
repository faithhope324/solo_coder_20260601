import urllib.request
import json

r = urllib.request.urlopen('http://127.0.0.1:5000/api/anomaly')
data = json.loads(r.read())
print('Anomaly API test:')
print(f'  Total: {data["total"]}')
print(f'  First item: {data["data"][0]}')
