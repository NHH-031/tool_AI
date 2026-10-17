import requests

scenes = [
    (2, """Masterpiece storybook watercolor and ink illustration, crisp expressive dark ink contours and rich vibrant harmonious colors on warm vintage cream paper #F5EBD7. A nostalgic Vietnamese neighborhood grocery store filled with hanging snacks and dry goods. Uncle Sau, an elderly shopkeeper with glasses slid down his nose, sitting on a folding canvas chair waving a handwoven palm leaf fan. Beside him, an oversized chubby calico cat named Tun sleeps heavily on a burlap rice sack. Hai stands gaunt and weary, leaning desperately against the glass display counter, pointing pleadingly at fresh baguettes and soy milk. Clear distinct contour lines, smooth connected ink outlines, rich watercolor fills, high detail, 1080p widescreen, no text"""),
    (3, """Masterpiece storybook watercolor and ink illustration, crisp expressive dark ink contours and rich vibrant harmonious colors on warm vintage cream paper #F5EBD7. A dramatic, comical indoor chaos scene inside a dim grocery warehouse. Hai falling flat on his back on tiled floor, legs up, wildly swinging a traditional straw broom in panic. A large brown rat darting away as an old burlap sack of rice husks tumbles down; at the warehouse threshold, the chubby cat leaps in startled fright, knocking an aluminum water bowl that splashes onto Uncle Sau's bare foot in the background. Expressive motion lines and vibrant dynamic splatters. Clear distinct contour lines, smooth connected ink outlines, rich watercolor fills, high detail, 1080p widescreen, no text"""),
    (4, """Masterpiece storybook watercolor and ink illustration, crisp expressive dark ink contours and rich vibrant harmonious colors on warm vintage cream paper #F5EBD7. A heartwarming sunny porch scene outside the rustic grocery store. Hai sits happily on the stone doorstep, covered in dust and cobwebs, biting greedily into a crusty Vietnamese banh mi sandwich loaded with pate, herbs, and Vietnamese pork sausage, a clear bag of iced soy milk beside him. The fat calico cat Tun rubs affectionately against his leg as Hai tosses it a tiny meat piece. In the background, Uncle Sau leans against the wooden doorframe with arms crossed, smiling fondly while pointing to a yard broom. Clear distinct contour lines, smooth connected ink outlines, rich watercolor fills, high detail, 1080p widescreen, no text""")
]

for idx, p in scenes:
    print(f"Generating scene {idx}...")
    payload = {
        "scene_id": f"scene-{idx}",
        "scene_index": idx,
        "prompt": p,
        "project_id": "test_hai_story",
        "force_regenerate": True
    }
    r = requests.post("http://127.0.0.1:8000/storyboard/generate-image", json=payload, timeout=90)
    print(f"Scene {idx}: status={r.status_code}, url={r.json().get('image_url')}")
