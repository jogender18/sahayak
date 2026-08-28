"""
Take a full-page screenshot using Chrome CDP (via --screenshot with virtual time).
Then use Pillow to crop out specific form sections for display.
"""
import subprocess
import time
import os
import shutil
from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = os.path.dirname(os.path.abspath(__file__))
BRAIN = r"C:\Users\Rohit\.gemini\antigravity\brain\3d00a79a-8174-4a9e-89ef-0ec63ff87fa2"
URL = "http://127.0.0.1:5000/"

# 1. Take a tall full-page screenshot at mobile width
out_full = os.path.join(BASE, "voice_fullpage.png")
cmd = [
    CHROME,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--window-size=480,3200",   # very tall window captures full page
    f"--screenshot={out_full}",
    "--hide-scrollbars",
    URL,
]
subprocess.run(cmd, capture_output=True, timeout=30)
time.sleep(2)

if not os.path.exists(out_full):
    print("FAILED: no screenshot captured")
    raise SystemExit(1)

img = Image.open(out_full)
w, h = img.size
print(f"Full page size: {w}×{h}px")

# 2. Define crop zones (proportional to a ~3200px tall render)
# Adjust these bounds based on actual height
zones = {
    # Show top of form with owner/worker fields + mic buttons
    "voice_crop_owner_section.png":  (0, 250, w, 820),
    # Show work description section with mic button
    "voice_crop_work_desc.png":      (0, 820, w, 1200),
    # Show wage amount + mic button
    "voice_crop_wage_section.png":   (0, 1200, w, 1580),
    # Show penalty + submit
    "voice_crop_penalty_submit.png": (0, 1580, w, 1960),
}

for fname, box in zones.items():
    # Clamp to actual image height
    clamped = (box[0], min(box[1], h-1), box[2], min(box[3], h))
    if clamped[1] >= clamped[3]:
        print(f"SKIP {fname} (out of bounds)")
        continue
    crop = img.crop(clamped)
    dst = os.path.join(BASE, fname)
    crop.save(dst)
    shutil.copy2(dst, os.path.join(BRAIN, fname))
    print(f"Saved & copied: {fname}  ({crop.size[0]}×{crop.size[1]})")

shutil.copy2(out_full, os.path.join(BRAIN, "voice_fullpage.png"))
print("Done.")
