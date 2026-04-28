import requests
import json
import time

API_BASE = 'http://127.0.0.1:8000/api/v1'
PDF_PATH = 'tests/imanuvilov1998lipschitz.pdf'
TARGET_LANGUAGE = 'French'
STYLE = 'literary'

# Step 1: Upload file
print(f"Uploading {PDF_PATH}...")
with open(PDF_PATH, 'rb') as f:
    r = requests.post(
        f'{API_BASE}/translate/file',
        files={'file': (PDF_PATH.split('/')[-1], f, 'application/pdf')},
        params={'target_language': TARGET_LANGUAGE, 'style': STYLE}
    )

data = r.json()
job_id = data['job_id']
print(f"Job started: {job_id}")
print(f"Status: {data['status']}")
print()

# Step 2: Poll until done
for i in range(40):
    time.sleep(15)
    r = requests.get(f'{API_BASE}/jobs/{job_id}')
    j = r.json()
    print(f"[{i+1}] status={j['status']} | chapters={j['completed_chapters']}/{j['chapter_count']} | tokens={j['total_tokens']} | progress={j['progress_percent']}%")

    if j['status'] == 'completed':
        print()
        print("TRANSLATION COMPLETE:")
        print(json.dumps(j, indent=2))
        print()
        print(f"Download URL: {API_BASE}/jobs/{job_id}/download")
        break
    elif j['status'] == 'failed':
        print()
        print("FAILED:")
        print(json.dumps(j, indent=2))
        break
