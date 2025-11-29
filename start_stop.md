# In CMD
## start the app:

- cmd windows
- cd C:\Users\marku\Documents\2025\93_Project_AI\repos\asiaspanel
- scripts\run_local.bat
## stop the app:
-scripts\stop_local.bat


# in terminal with conda test TTS
## activate
- conda activate asia_02
## test TTS
- curl -v -X POST http://127.0.0.1:8001/api/tts -H "Content-Type: application/json" -d "{\"text\":\"Hello from test\",\"voice\":\"default\",\"format\":\"wav\"}"


