import os
import requests
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

IPFS_API_URL = "http://127.0.0.1:5001/api/v0/add"

def upload_to_ipfs(file):
    # Save file temporarily to disk
    temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    print(f"Saving file temporarily at: {temp_file_path}")

    with default_storage.open(temp_file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # Read file and send it to IPFS
    with open(temp_file_path, 'rb') as f:
        files = {'file': (file.name, f)}
        response = requests.post(IPFS_API_URL, files=files)

    # Debugging Info
    print(f"IPFS Upload Status: {response.status_code}")
    print(f"Response Text: {response.text}")

    if response.status_code == 200:
        ipfs_response = response.json()
        cid = ipfs_response['Hash']
        print(f"CID returned: {cid}")

        # Clean up the temporary file
        os.remove(temp_file_path)
        return cid
    else:
        raise Exception(f"Failed to upload to IPFS. Response: {response.text}")
