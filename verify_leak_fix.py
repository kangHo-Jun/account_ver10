import time
from core.browser import BrowserManager
from core.logger import logger
import subprocess

def count_chrome():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe', '/NH'], capture_output=True, text=True)
    if "chrome.exe" not in result.stdout:
        return 0
    return len([line for line in result.stdout.splitlines() if "chrome.exe" in line])

def test_leak_fix():
    print(f"Initial Chrome count: {count_chrome()}")
    
    browser = BrowserManager()
    
    print("Starting browser...")
    browser.start(headless=True)
    print(f"Chrome count during run: {count_chrome()}")
    
    time.sleep(3)
    
    print("Closing browser...")
    browser.close()
    
    time.sleep(2)
    final_count = count_chrome()
    print(f"Final Chrome count: {final_count}")
    
    if final_count == 0:
        print("SUCCESS: No Chrome leaks detected.")
    else:
        print(f"WARNING: {final_count} Chrome processes still exist.")

if __name__ == "__main__":
    test_leak_fix()
