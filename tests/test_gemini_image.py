import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "").strip()
client = genai.Client(api_key=key)

test_models = [
    "imagen-3.0-generate-002",
    "imagen-3.0-fast-generate-001",
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
]

for m in test_models:
    try:
        print(f"Testing model: {m}...")
        r = client.models.generate_images(
            model=m,
            prompt="Whiteboard doodle illustration of a young man lying on a thin mattress in a messy rented room, warm vintage cream paper #F5EBD7, crisp dark ink outlines",
            config=dict(number_of_images=1, aspect_ratio="16:9"),
        )
        if r.generated_images:
            print(f"{m}: SUCCESS! Got image of size {len(r.generated_images[0].image.image_bytes)} bytes!")
            out_name = f"output/test_{m.replace('.', '_')}.png"
            with open(out_name, "wb") as f:
                f.write(r.generated_images[0].image.image_bytes)
            print(f"Saved to {out_name}")
            break
    except Exception as e:
        print(f"{m}: FAILED -> {e}")
