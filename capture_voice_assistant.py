"""
Automated screenshot generator for the conversational full-screen voice assistant.
Captures the three main voice assistant interface states.
"""
import subprocess
import time
import os
import shutil

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = os.path.dirname(os.path.abspath(__file__))
BRAIN = r"C:\Users\Rohit\.gemini\antigravity\brain\3d00a79a-8174-4a9e-89ef-0ec63ff87fa2"
BASE_URL = "http://127.0.0.1:5000/"

def capture(url_suffix, filename):
    out_path = os.path.join(BASE, filename)
    if os.path.exists(out_path):
        os.remove(out_path)
    
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=480,850",
        f"--screenshot={out_path}",
        "--hide-scrollbars",
        BASE_URL + url_suffix
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)
    time.sleep(2)
    
    if os.path.exists(out_path):
        shutil.copy2(out_path, os.path.join(BRAIN, filename))
        print(f"Captured & copied: {filename}")
    else:
        print(f"FAILED to capture: {filename}")

print("Capturing voice assistant states...")
capture("?mock_voice_state=1", "voice_assistant_start.png")
capture("?mock_voice_state=2", "voice_assistant_work_desc.png")
capture("?mock_voice_state=3", "voice_assistant_wage.png")
print("Done.")
