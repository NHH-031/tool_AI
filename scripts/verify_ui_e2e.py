# -*- coding: utf-8 -*-
"""
Playwright E2E UI verification for Phase 10.2:
Tests New Video flow in browser, creating Job A (Dog/Ball) and Job B (Earth/Sun).
Captures screenshots and validates elements on the Review screen.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_DIR = Path(r"C:\Users\ACER\.gemini\antigravity-ide\brain\ae80ef99-83b9-425a-8f28-d25759118500")

async def run_e2e():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("[E2E] 1. Navigating to http://localhost:3000/")
        await page.goto("http://localhost:3000/", wait_until="networkidle")

        # -------------------------------------------------------------
        # TEST 1: JOB A - DOG & BALL
        # -------------------------------------------------------------
        print("[E2E] 2. Testing Job A: Dog and Ball")
        # Click Create Video tab
        await page.locator("button:has-text('Create Video')").first.click()
        await page.wait_for_selector("#input-create-title")

        # Check default mode
        mode_btn = page.locator("#btn-mode-script")
        await mode_btn.click()

        # Fill Title & Script
        await page.fill("#input-create-title", "Chó Đuổi Bóng")
        await page.fill("#input-create-prompt", "Con chó đang chạy theo quả bóng.")

        # Click Generate Video
        await page.click("#btn-generate-pipeline")
        print("[E2E] Submitted Job A, waiting for generation...")

        # Wait for Review screen
        await page.wait_for_selector("#review-video-player", timeout=60000)
        await page.wait_for_selector("#qa-overall-badge", timeout=10000)
        await asyncio.sleep(2)  # Wait for rendering

        # Take screenshot of Review Screen for Job A
        shot_a = ARTIFACT_DIR / "e2e_review_job_a_dog.png"
        await page.screenshot(path=str(shot_a), full_page=True)
        print(f"[E2E] Screenshot saved: {shot_a.name}")

        # Check script text in page content
        content_a = await page.content()
        assert "Con chó đang chạy theo quả bóng." in content_a, "Job A script text not found on review screen"
        print("[E2E] Job A script text verified on review screen!")

        # Check video src
        video_src_a = await page.get_attribute("#review-video-player", "src")
        print(f"[E2E] Job A video src: {video_src_a}")
        assert "job-" in video_src_a, f"Unexpected video src: {video_src_a}"
        assert "monkey_banana_e2e" not in video_src_a, "Job A must NOT point to monkey regression video"

        # Click Visual Entities tab
        await page.click("#subtab-entities")
        await page.wait_for_selector("#review-entities-grid", timeout=10000)
        await asyncio.sleep(1)

        entities_text_a = await page.locator("#review-entities-grid").inner_text()
        print(f"[E2E] Job A Entities box:\n{entities_text_a}")
        assert "dog" in entities_text_a.lower() or "chó" in entities_text_a.lower(), "Dog entity missing in Job A"
        assert "monkey" not in entities_text_a.lower(), "Monkey leaked into Job A!"
        assert "banana" not in entities_text_a.lower(), "Banana leaked into Job A!"

        # -------------------------------------------------------------
        # TEST 2: JOB B - EARTH & SUN
        # -------------------------------------------------------------
        print("\n[E2E] 3. Testing Job B: Earth Orbiting Sun")
        # Click Create Video in nav
        await page.click("#nav-create")
        await page.wait_for_selector("#input-create-title")

        # Fill Title & Script
        await page.fill("#input-create-title", "Hệ Mặt Trời")
        await page.fill("#input-create-prompt", "Trái Đất quay quanh Mặt Trời.")

        # Click Generate Video
        await page.click("#btn-generate-pipeline")
        print("[E2E] Submitted Job B, waiting for generation...")

        # Wait for Review screen
        await page.wait_for_selector("#review-video-player", timeout=60000)
        await page.wait_for_selector("#qa-overall-badge", timeout=10000)
        await asyncio.sleep(2)

        # Take screenshot of Review Screen for Job B
        shot_b = ARTIFACT_DIR / "e2e_review_job_b_earth.png"
        await page.screenshot(path=str(shot_b), full_page=True)
        print(f"[E2E] Screenshot saved: {shot_b.name}")

        # Check script text in page content
        content_b = await page.content()
        assert "Trái Đất quay quanh Mặt Trời." in content_b, "Job B script text not found on review screen"
        print("[E2E] Job B script text verified on review screen!")

        # Check video src
        video_src_b = await page.get_attribute("#review-video-player", "src")
        print(f"[E2E] Job B video src: {video_src_b}")
        assert video_src_b != video_src_a, "Job B must have distinct video src from Job A!"
        assert "monkey_banana_e2e" not in video_src_b, "Job B must NOT point to monkey regression video"

        # Click Visual Entities tab
        await page.click("#subtab-entities")
        await page.wait_for_selector("#review-entities-grid", timeout=10000)
        await asyncio.sleep(1)

        entities_text_b = await page.locator("#review-entities-grid").inner_text()
        print(f"[E2E] Job B Entities box:\n{entities_text_b}")
        assert "sun" in entities_text_b.lower() or "mặt trời" in entities_text_b.lower(), "Sun entity missing in Job B"
        assert "earth" in entities_text_b.lower() or "trái đất" in entities_text_b.lower(), "Earth entity missing in Job B"
        assert "dog" not in entities_text_b.lower(), "Dog leaked into Job B!"
        assert "monkey" not in entities_text_b.lower(), "Monkey leaked into Job B!"

        print("\n[E2E] ALL UI BROWSER VERIFICATIONS PASSED!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_e2e())
