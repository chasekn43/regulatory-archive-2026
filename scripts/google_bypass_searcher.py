from DrissionPage import ChromiumPage, ChromiumOptions
import sys
import os
import time
import random
import urllib.parse
import tempfile
import shutil
from fireprox_config import get_base_url

# Add solver path to import RecaptchaSolver
sys.path.append(r"c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\403_tools\GoogleRecaptchaBypass")
try:
    from RecaptchaSolver import RecaptchaSolver
except ImportError as e:
    print("Warning: Could not import RecaptchaSolver:", e)

def search_google_via_browser(query, worker_id="0"):
    """Executes a Google Search query via automated Chromium, solving any CAPTCHA if encountered."""
    CHROME_ARGUMENTS = [
        "--no-first-run",
        "--force-color-profile=srgb",
        "--metrics-recording-only",
        "--password-store=basic",
        "--use-mock-keychain",
        "--export-tagged-pdf",
        "--no-default-browser-check",
        "--disable-background-mode",
        "--deny-permission-prompts",
        "--disable-gpu",
        "--accept-lang=en-US",
        "--disable-usage-stats",
        "--disable-crash-reporter",
        "--no-sandbox",
        "--page-load-strategy=eager"
    ]
    
    options = ChromiumOptions()
    for argument in CHROME_ARGUMENTS:
        options.set_argument(argument)
    
    def get_free_port():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    # Configure custom port and explicit browser path to avoid locks
    options.set_browser_path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    options.set_local_port(get_free_port())
    options.headless(True)
    
    # Set unique user data path based on worker_id to prevent folder locks and sticky fingerprints
    temp_dir = os.environ.get('TEMP', os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp'))
    user_data_dir = tempfile.mkdtemp(prefix=f"dp_profile_{worker_id}_", dir=temp_dir)
    options.set_paths(user_data_path=user_data_dir)
        
    driver = ChromiumPage(addr_or_opts=options)
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=10"
        print(f"[Solver] Loading Google Search URL: {url}", file=sys.stderr)
        driver.get(url)
        time.sleep(2)
        
        # Check if Google redirected us to the CAPTCHA page
        is_captcha = "sorry/index" in driver.url or driver.ele("#recaptcha") or driver.ele(".g-recaptcha")
        if is_captcha:
            print("[Solver] Google reCAPTCHA block encountered. Bypassing...", file=sys.stderr)
            try:
                solver = RecaptchaSolver(driver)
                solver.solveCaptcha()
                print("[Solver] reCAPTCHA successfully bypassed!", file=sys.stderr)
                time.sleep(1)
            except Exception as e:
                screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captcha_error.png")
                try:
                    driver.get_screenshot(path=screenshot_path)
                    print(f"[Solver ERROR] Captcha solve failed: {e}. Saved screenshot to: {screenshot_path}", file=sys.stderr)
                except Exception as ex_screen:
                    print(f"[Solver ERROR] Captcha solve failed: {e} (Screenshot failed: {ex_screen})", file=sys.stderr)
                raise e
            
        html = driver.html
        return html
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        # Clean up temp folder
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:
            pass

if __name__ == "__main__":
    if len(sys.argv) > 2:
        worker_id = sys.argv[1]
        query = " ".join(sys.argv[2:])
    elif len(sys.argv) > 1:
        worker_id = "0"
        query = " ".join(sys.argv[1:])
    else:
        worker_id = "0"
        query = "Chase Kinslow Affirm evidence vault"
        
    print(f"Testing Google bypass search for query: '{query}' (Worker ID: {worker_id})", file=sys.stderr)
    html = search_google_via_browser(query, worker_id)
    if html:
        sys.stdout.write(html)
        print(f"Bypass search completed. Output length: {len(html)} characters.", file=sys.stderr)
    else:
        print("[FAILED] Bypassed HTML is empty or invalid.", file=sys.stderr)
        sys.exit(1)
