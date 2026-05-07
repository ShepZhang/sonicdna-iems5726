"""Capture submission screenshots from the live Streamlit app.

Outputs to ``project_root/screenshots/`` six PNGs:

  01_dashboard.png      Full Dashboard tab (MoodPrint + Music MBTI + Top-10 recs)
  02_universes.png      Full Parallel Universes tab with Synthwave selected
  03_insights.png       Full Insights tab (PCA + radar + donut)
  04_about.png          Full About tab
  05_moodprint.png      Tight crop of just the spinning vinyl MoodPrint
  06_sidebar.png        Sidebar (sample selector + tab blurb) for the report

Pre-requisite: streamlit is running at http://localhost:8501
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8501"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Slightly wider than a typical laptop to make sure both Dashboard
        # columns (MoodPrint + MBTI card) are fully visible without
        # horizontal scroll.
        ctx = browser.new_context(
            viewport={"width": 1480, "height": 1100},
            device_scale_factor=2,    # retina-ish output for the report
        )
        page = ctx.new_page()
        page.set_default_timeout(60_000)

        # ---------- initial load ----------
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".sd-print-frame img")
        # Give the breathing CSS animation a tick to settle on a flattering frame.
        page.wait_for_timeout(2000)

        # Pick the most visually rich sample so the print is not blank.
        page.get_by_role("combobox").first.click()
        page.wait_for_timeout(300)
        page.get_by_role("option", name="Workout Beast Mode").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(".sd-print-frame img")
        page.wait_for_timeout(2500)

        # ---------- 1. Dashboard tab full page ----------
        print("[1/6] Dashboard …")
        page.screenshot(path=str(OUT / "01_dashboard.png"), full_page=True)

        # ---------- 5. Tight MoodPrint crop ----------
        print("[5/6] MoodPrint crop …")
        page.locator(".sd-print-frame").first.screenshot(
            path=str(OUT / "05_moodprint.png"),
        )

        # ---------- 2. Parallel Universes tab ----------
        print("[2/6] Parallel Universes …")
        page.get_by_role("tab", name="Parallel Universes").click()
        # Streamlit lazy-mounts the radar + recommendation table; a fixed
        # delay is more reliable than waiting on a selector that already
        # exists from the cached Dashboard tab.
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(4500)
        page.screenshot(path=str(OUT / "02_universes.png"), full_page=True)

        # ---------- 3. Insights tab ----------
        print("[3/6] Insights …")
        page.get_by_role("tab", name="Insights").click()
        # PCA scatter has 8000 markers; let it actually paint.
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT / "03_insights.png"), full_page=True)

        # ---------- 4. About tab ----------
        print("[4/6] About …")
        page.get_by_role("tab", name="About").click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "04_about.png"), full_page=True)

        # ---------- 6. Sidebar only (smaller, optional figure) ----------
        print("[6/6] Sidebar …")
        # Go back to the dashboard so the sidebar shows the full active state.
        page.get_by_role("tab", name="Dashboard").click()
        page.wait_for_timeout(800)
        sidebar = page.locator("[data-testid='stSidebar']").first
        sidebar.screenshot(path=str(OUT / "06_sidebar.png"))

        ctx.close()
        browser.close()

    print()
    print(f"[done] {len(list(OUT.glob('*.png')))} PNGs saved under {OUT}")
    for f in sorted(OUT.glob("*.png")):
        size_kb = f.stat().st_size / 1024
        print(f"   {f.name:<24s}  {size_kb:>7.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
