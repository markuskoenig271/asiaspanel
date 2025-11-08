import json
import urllib.request

URL = "http://127.0.0.1:8002/api/translate"

data = json.dumps({"text": "hello world", "target": "de"}).encode("utf-8")
req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})

with urllib.request.urlopen(req, timeout=10) as resp:
    body = resp.read().decode("utf-8")
    print("Response:", body)
