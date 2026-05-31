"""Capture real screenshots of the running DocChat app via Playwright.

The FastAPI app must already be running on the given base URL:
    uvicorn app:app --port 8780
    python tools/shoot.py http://localhost:8780
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


def ask(page, question: str) -> None:
    box = page.locator("#q")
    box.fill(question)
    page.locator("#composer button").click()
    page.wait_for_selector(".msg.bot .cite", timeout=10000)
    time.sleep(0.6)


def main(base: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = base.rstrip("/")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900},
                                device_scale_factor=2)
        page.goto(base + "/", wait_until="networkidle")
        page.wait_for_selector("#composer")
        time.sleep(0.6)

        # 1) Landing (empty state) — doc list + suggestions.
        page.screenshot(path=str(OUT / "home.png"))
        print("saved home.png")

        # 2) A cited answer (and a second question for a fuller transcript).
        ask(page, "How many vacation days do employees get?")
        ask(page, "How do I reset the Widget 3000?")
        page.screenshot(path=str(OUT / "chat_answer.png"), full_page=True)
        print("saved chat_answer.png")

        browser.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8780")
