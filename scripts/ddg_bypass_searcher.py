from DrissionPage import ChromiumPage, ChromiumOptions
import sys
import os
import time
import urllib.parse
import tempfile
import shutil

def search_ddg_via_browser(query, worker_id="0"):
    """Executes a DuckDuckGo Search query via automated Chromium to bypass TLS fingerprint blocks."""
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

    options.set_browser_path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    options.set_local_port(get_free_port())
    options.headless(True)
    
    # Use unique temp directory to prevent profile reuse/fingerprint caching
    temp_dir = os.environ.get('TEMP', os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp'))
    user_data_dir = tempfile.mkdtemp(prefix=f"dp_profile_ddg_{worker_id}_", dir=temp_dir)
    options.set_paths(user_data_path=user_data_dir)
        
    driver = ChromiumPage(addr_or_opts=options)
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        print(f"[DDG Bypass] Loading DuckDuckGo: {url}", file=sys.stderr)
        driver.get(url)
        time.sleep(2)
        
        # Check for CAPTCHA block
        html = driver.html
        if "bots use duckduckgo" in html.lower():
            print("[DDG Bypass ERROR] DuckDuckGo CAPTCHA page triggered. Please connect to a clean IP/VPN.", file=sys.stderr)
            sys.exit(2)  # Exit code 2 indicates CAPTCHA block
            
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
        query = "Chase Kinslow Affirm"
        
    html = search_ddg_via_browser(query, worker_id)
    if html:
        sys.stdout.write(html)
        sys.exit(0)
    else:
        sys.exit(1)
