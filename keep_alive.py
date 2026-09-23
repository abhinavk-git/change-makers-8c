import os
import time
import urllib.request

def ping_app():
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        print("No RENDER_EXTERNAL_URL found, using localhost fallback but this may not prevent sleep on Render.")
        url = f"http://localhost:{os.environ.get('PORT', '8501')}"
        # On Render, pinging localhost doesn't keep it awake, it must be the external URL.
        # But we'll try it anyway just so the script doesn't completely fail.
        
    print(f"Starting keep-alive for {url}")
    while True:
        try:
            # Sleep for 14 minutes (840 seconds) to be just under the 15 minute limit
            time.sleep(840)
            req = urllib.request.Request(url, headers={'User-Agent': 'KeepAlive/1.0'})
            with urllib.request.urlopen(req) as response:
                print(f"Keep-alive pinged {url}, status code: {response.getcode()}")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")

if __name__ == "__main__":
    ping_app()
