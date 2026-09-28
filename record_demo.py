import os
import time
import shutil
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path("/config/.gemini/antigravity/brain/990fd4a3-0273-4657-aab8-c65cdcdf2d48")
TEMP_VIDEO_DIR = ARTIFACT_DIR / "video_temp"
FINAL_WEBM_PATH = ARTIFACT_DIR / "wanderlust_concierge_demo.webm"
FINAL_MP4_PATH = ARTIFACT_DIR / "wanderlust_concierge_demo.mp4"

TEMP_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

APP_URL = "https://wanderlust-concierge-frontend-269805253771.us-east1.run.app"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(TEMP_VIDEO_DIR),
            record_video_size={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        print(f"Navigating to {APP_URL}...")
        page.goto(APP_URL, wait_until="networkidle")
        time.sleep(2)
        
        # 1. First interaction: Core capability (Travel Itinerary & Budget Planning)
        print("Sending prompt 1...")
        prompt1 = "Plan a 3-day trip to Tokyo with budget calculation"
        page.fill("#input", prompt1)
        time.sleep(1)
        page.keyboard.press("Enter")
        
        print("Waiting for agent response 1...")
        page.wait_for_selector(".msg.agent", timeout=60000)
        time.sleep(7)  # Pause to showcase the itinerary card
        
        # 2. Second interaction: Richer prompt showing tool calls, database lookup & scenic visual image
        print("Sending prompt 2...")
        prompt2 = "Find top rated stays in Kyoto and generate a high quality scenic image visual of Fushimi Inari shrine."
        page.fill("#input", prompt2)
        time.sleep(1)
        page.keyboard.press("Enter")
        
        print("Waiting for agent response 2...")
        page.wait_for_function("document.querySelectorAll('.msg.agent').length >= 2", timeout=90000)
        time.sleep(10)  # Pause to showcase the generated visual image and database stay details
        
        # Close context to finish recording
        video_path = page.video.path()
        context.close()
        browser.close()
        
        if os.path.exists(video_path):
            shutil.move(video_path, str(FINAL_WEBM_PATH))
            print(f"WebM demo video saved to {FINAL_WEBM_PATH}")
            
            # Attempt converting to MP4 if ffmpeg is available
            try:
                ffmpeg_bin = shutil.which("ffmpeg") or str(Path.home() / ".cache/ms-playwright/ffmpeg-1011/ffmpeg-linux")
                if os.path.exists(ffmpeg_bin) or shutil.which("ffmpeg"):
                    cmd = [ffmpeg_bin or "ffmpeg", "-y", "-i", str(FINAL_WEBM_PATH), "-c:v", "libx264", str(FINAL_MP4_PATH)]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"MP4 demo video converted and saved to {FINAL_MP4_PATH}")
            except Exception as e:
                print(f"MP4 conversion skipped: {e}")
        else:
            print("Recorded video file not found!")

if __name__ == "__main__":
    run()
