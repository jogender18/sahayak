"""
Screenshot the voice-input form at several states using Chrome in headless mode.
Captures:
  1. The full form with mic buttons visible
  2. Scroll to wage section showing wage mic button
  3. Scroll to work description section
"""
import subprocess
import time
import os
import shutil

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BRAIN_DIR = r"C:\Users\Rohit\.gemini\antigravity\brain\3d00a79a-8174-4a9e-89ef-0ec63ff87fa2"
BASE_URL = "http://127.0.0.1:5000"

def screenshot(url, out_path, delay=2, window_size="450,900", scroll_y=0):
    """Use Chrome headless to screenshot a page."""
    js_scroll = f"--run-chrome-js=window.scrollTo(0,{scroll_y})" if scroll_y else ""
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--window-size={window_size}",
        f"--screenshot={out_path}",
        "--hide-scrollbars",
        url,
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)
    time.sleep(delay)
    return os.path.exists(out_path)

# 1. Full form - top section (owner/worker)
top_path = os.path.join(os.path.dirname(__file__), "voice_form_top.png")
ok = screenshot(BASE_URL, top_path, delay=3, window_size="480,960", scroll_y=0)
print(f"Top screenshot: {'OK' if ok else 'FAILED'}")

# 2. Mobile view of wage + mic button area — screenshot full page at narrow width
wage_path = os.path.join(os.path.dirname(__file__), "voice_form_wage.png")
ok2 = screenshot(BASE_URL + "/#wage_amount", wage_path, delay=3, window_size="480,960")
print(f"Wage section screenshot: {'OK' if ok2 else 'FAILED'}")

# Copy to brain dir
for src, dst in [(top_path, "voice_form_top.png"), (wage_path, "voice_form_wage.png")]:
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(BRAIN_DIR, dst))
        print(f"Copied {dst} to brain dir")
