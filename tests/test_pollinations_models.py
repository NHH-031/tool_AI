import urllib.parse
import requests

p = "A young man sitting in front of a rustic grocery store cabinet with bread and snacks, whiteboard doodle on cream paper"
encoded = urllib.parse.quote(p)

for model in ["", "turbo", "flux", "flux-realism", "flux-anime"]:
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true"
    if model:
        url += f"&model={model}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        print(f"Model '{model}': status={r.status_code}, len={len(r.content)}")
    except Exception as e:
        print(f"Model '{model}': error={e}")
