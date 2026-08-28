import os
import re
import sys
import time
import subprocess
import urllib.request

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_EXE = os.path.join(SCRATCH_DIR, "cloudflared.exe")
PUBLIC_URL_FILE = os.path.join(SCRATCH_DIR, "public_url.txt")

def start_tunnel():
    print("Starting Cloudflare Tunnel to expose port 5000 publicly...")
    cmd = [CLOUDFLARED_EXE, "tunnel", "--url", "http://127.0.0.1:5000"]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=SCRATCH_DIR
    )

    public_url = None
    pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    start_time = time.time()
    while time.time() - start_time < 30:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            continue
        
        # Look for the URL
        match = pattern.search(line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        print("Failed to find Cloudflare Tunnel URL within 30 seconds.")
        proc.terminate()
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"  SAHAYAK PUBLIC LIVE URL:")
    print(f"  {public_url}")
    print(f"=======================================================\n")

    # Save to public_url.txt — overwrite any previous session's stale URL
    with open(PUBLIC_URL_FILE, "w") as f:
        f.write(public_url + "\n")
    print(f"Saved public URL to {PUBLIC_URL_FILE}")

    # Verify public access
    time.sleep(3)
    try:
        req = urllib.request.Request(
            public_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                print(f"Verified: {public_url} is LIVE and publicly accessible (HTTP 200 OK)!")
    except Exception as e:
        print(f"Verification notice: {e}")

    # Keep running — clear the URL file on clean shutdown so no stale URL persists
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    finally:
        # Remove the stale URL so the next session starts clean
        if os.path.exists(PUBLIC_URL_FILE):
            os.remove(PUBLIC_URL_FILE)
            print("Tunnel closed — cleared public_url.txt to avoid stale URL on next start.")

if __name__ == "__main__":
    start_tunnel()
