"""
Simple script to test uploading a small blob to Azure Blob Storage (or Azurite) using
AZURE_STORAGE_CONNECTION_STRING from environment (or .env).

Usage:
  set AZURE_STORAGE_CONNECTION_STRING=...   (or put in .env and use python-dotenv)
  python scripts/test_blob_upload.py

This will create the container (if missing) and upload a small test blob named test-blob-<hex>.txt
and print the blob URL.
"""
import os
import uuid
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

CONN = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
if not CONN:
    print('No AZURE_STORAGE_CONNECTION_STRING configured in environment or .env')
    raise SystemExit(2)

try:
    from azure.storage.blob import BlobServiceClient
except Exception as e:
    print('azure-storage-blob package is required. Install it in your asia_02 env: pip install azure-storage-blob')
    raise

client = BlobServiceClient.from_connection_string(CONN)
container_name = os.getenv('AZURE_TTS_CONTAINER', 'tts-audio')
try:
    client.create_container(container_name)
    print('Created container', container_name)
except Exception:
    print('Container exists or could not be created (continuing)')

blob_name = f"test-blob-{uuid.uuid4().hex}.txt"
content = b"This is a test blob from asiaspanel test_blob_upload.py\n"
blob_client = client.get_blob_client(container=container_name, blob=blob_name)
try:
    blob_client.upload_blob(content, overwrite=True)
    print('Uploaded blob:', blob_name)
    print('Blob URL:', blob_client.url)
except Exception as e:
    print('Upload failed:', e)
    raise
