import urllib.request, json, sys

url = 'http://127.0.0.1:8002/api/tts'
data = json.dumps({'text':'Hello from OpenAI TTS test','voice':'alloy','format':'mp3'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(resp.read().decode())
except Exception as e:
    print('ERROR', repr(e))
    sys.exit(1)
