"""
WAF/CDN Bypass Headers Module - Extracted from hashtag-fuzz.

Provides randomized WAF/CDN bypass headers that can be injected into
urllib.request calls to evade IP-based rate limiting and WAF detection.

Usage:
    from waf_bypass_headers import get_bypass_headers, apply_bypass_headers
    
    # Get headers as a dict for urllib.request.Request
    headers = get_bypass_headers(mode='pro')
    req = urllib.request.Request(url)
    apply_bypass_headers(req, mode='pro')
"""
import random
import string
from datetime import datetime, timedelta

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0",
]


def _generate_random_ip():
    """Generate a random internal/external IP for header spoofing."""
    range_type = random.choice(["public", "public", "public", "127", "10", "172", "192"])
    if range_type == "public":
        return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    elif range_type == "127":
        return f"127.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    elif range_type == "10":
        return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    elif range_type == "172":
        return f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    elif range_type == "192":
        return f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"


def _random_string(length=None):
    """Generate a random alphanumeric string."""
    if length is None:
        length = random.randint(4, 8)
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def get_bypass_headers(mode='common', url=None):
    """Get WAF/CDN bypass headers as a dictionary.
    
    Modes (from hashtag-fuzz):
        'entry'   - Minimal headers, low evasion (7 headers)
        'common'  - Standard bypass set (11 headers)
        'pro'     - Extended bypass with forwarding chains (13 headers)
        'prime'   - Maximum evasion, all known bypass headers (16 headers)
    
    Args:
        mode: Bypass aggressiveness level
        url: Optional target URL for Origin/Referer headers
        
    Returns:
        dict of header name -> value
    """
    random_ip = _generate_random_ip()
    random_ip2 = _generate_random_ip()
    
    # Core IP spoofing headers (all modes)
    headers = {
        "X-Forwarded-For": random_ip,
        "X-Forwarded-Host": random_ip,
        "X-Remote-IP": random_ip,
        "X-Originating-IP": random_ip,
        "X-Remote-Addr": random_ip,
        "X-Client-IP": random_ip,
        "X-Host": random_ip,
    }
    
    if mode in ('common', 'pro', 'prime'):
        headers.update({
            "X-Real-IP": random_ip,
            "X-Forwarded-By": random_ip,
            "True-Client-IP": random_ip,
            "Client-IP": random_ip,
        })
    
    if mode in ('pro', 'prime'):
        headers.update({
            "X-Original-For": random_ip,
            "X-Forwarded": random_ip,
        })
    
    if mode == 'prime':
        headers.update({
            "X-Forwarded-Server": random_ip,
            "X-Forward-For": random_ip,
            "Forwarded": f"for={random_ip}; proto=https; by={random_ip2}",
        })
    
    # Browser-like headers (always added)
    headers["User-Agent"] = random.choice(USER_AGENTS)
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    headers["Accept-Language"] = random.choice([
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en,en-US;q=0.9",
    ])
    headers["Upgrade-Insecure-Requests"] = "1"
    headers["Sec-Fetch-Dest"] = "document"
    headers["Sec-Fetch-Mode"] = "navigate"
    headers["Sec-Fetch-Site"] = "none"
    headers["Sec-Fetch-User"] = "?1"
    headers["Sec-Ch-Ua-Platform"] = random.choice(['"Windows"', '"macOS"', '"Linux"'])
    headers["Sec-Ch-Ua-Mobile"] = "?0"
    headers["DNT"] = "1"
    headers["Cache-Control"] = random.choice(["max-age=0", "no-cache"])
    
    if url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        headers["Origin"] = f"{parsed.scheme}://{parsed.netloc}"
        headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
    
    return headers


def apply_bypass_headers(request, mode='common'):
    """Apply WAF bypass headers to a urllib.request.Request object.
    
    Args:
        request: urllib.request.Request object
        mode: Bypass aggressiveness ('entry', 'common', 'pro', 'prime')
    """
    headers = get_bypass_headers(mode=mode, url=request.full_url)
    for key, value in headers.items():
        request.add_header(key, value)
    return request


def get_random_query_suffix():
    """Generate a random query parameter to append to URLs for cache busting.
    
    Returns:
        str like '&xK3mQ=r8vPn' to append to URLs
    """
    key = _random_string(random.randint(3, 6))
    val = _random_string(random.randint(3, 6))
    return f"{key}={val}"
