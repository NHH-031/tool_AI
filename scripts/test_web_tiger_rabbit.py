import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def test_web_flow():
    out_dir = Path("output/ui_screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        print("[1] Navigating to http://localhost:3000 ...")
        page.goto("http://localhost:3000", wait_until="networkidle")
        time.sleep(2)

        # Click Create Video Tab
        print("[2] Navigating to Create Video tab ...")
        page.click("#nav-create")
        time.sleep(1)

        # Fill in the form
        print("[3] Filling prompt: 'trong khu rừng, con hổ đuổi con thỏ' ...")
        prompt_input = page.locator("#input-create-prompt")
        prompt_input.fill("trong khu rừng, con hổ đuổi con thỏ")

        title_input = page.locator("#input-create-title")
        title_input.fill("Hổ đuổi thỏ trong rừng")

        form_shot = out_dir / "01_create_form.png"
        page.screenshot(path=str(form_shot))
        print(f"    Saved form screenshot: {form_shot}")

        # Click Generate Video
        print("[4] Clicking Generate Video button ...")
        page.click("#btn-generate-pipeline")

        # Wait for the generation pipeline to complete and review screen to load
        print("[5] Waiting for generation pipeline to complete and render video ...")
        page.wait_for_selector("#review-video-player", timeout=90000)
        time.sleep(3)  # Give time for assets to render

        # Extract review screen information
        review_shot = out_dir / "02_review_screen.png"
        page.screenshot(path=str(review_shot), full_page=True)
        print(f"    Saved review screenshot: {review_shot}")

        # Check full script text
        script_elem = page.locator("text='trong khu rừng, con hổ đuổi con thỏ'").first
        has_script = script_elem.is_visible()
        print(f"[6] Script visible on page: {has_script}")

        # Check tags
        body_text = page.inner_text("body")
        has_tiger = "#tiger" in body_text or "tiger" in body_text or "hổ" in body_text
        has_rabbit = "#rabbit" in body_text or "rabbit" in body_text or "thỏ" in body_text
        has_forest = "#forest" in body_text or "forest" in body_text or "rừng" in body_text
        has_math = "#mathematics" in body_text

        print(f"[7] Tag verification:")
        print(f"    - Tiger present: {has_tiger}")
        print(f"    - Rabbit present: {has_rabbit}")
        print(f"    - Forest present: {has_forest}")
        print(f"    - Mathematics present (must be False): {has_math}")

        # Check QA badge
        qa_badge = page.locator("#qa-overall-badge")
        qa_text = qa_badge.inner_text() if qa_badge.is_visible() else "UNKNOWN"
        print(f"[8] QA Overall Badge: {qa_text}")

        # Check video src
        video_player = page.locator("#review-video-player")
        video_src = video_player.get_attribute("src")
        print(f"[9] Video src: {video_src}")

        # Click Play video and wait 2 seconds
        try:
            print("[10] Playing video preview ...")
            video_player.evaluate("v => v.play()")
            time.sleep(2)
            playing_shot = out_dir / "03_video_playing.png"
            page.screenshot(path=str(playing_shot))
            print(f"    Saved video playing screenshot: {playing_shot}")
        except Exception as e:
            print(f"    Play evaluation note: {e}")

        browser.close()

        result = {
            "has_script": has_script,
            "has_tiger": has_tiger,
            "has_rabbit": has_rabbit,
            "has_forest": has_forest,
            "has_mathematics": has_math,
            "qa_status": qa_text,
            "video_src": video_src,
            "screenshots": [str(form_shot), str(review_shot)]
        }
        print("FINAL_RESULT_JSON=" + json.dumps(result))

if __name__ == "__main__":
    test_web_flow()
