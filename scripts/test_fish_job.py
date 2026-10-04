import urllib.request
import json
from pathlib import Path

payload = {
    "title": "Con ca boi duoi bien",
    "script": "con cá đang bơi dưới biển",
    "input_mode": "SCRIPT",
    "auto_run": True,
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/jobs",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    job_id = data["id"]
    print("Job ID:", job_id)
    print("Status:", data["status"])

with urllib.request.urlopen(f"http://127.0.0.1:8000/jobs/{job_id}/review") as resp:
    rev = json.loads(resp.read().decode("utf-8"))
    print("Video URL:", rev.get("video_url"))
    print("Thumbnail URL:", rev.get("thumbnail_url"))
    print("QA Summary:", rev.get("qa_summary"))
