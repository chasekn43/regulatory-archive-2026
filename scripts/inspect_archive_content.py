import re
import sys
from html import unescape

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open('index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

print('=== ALL HEADINGS & SUBSECTIONS IN INDEX.HTML ===')
for m in re.finditer(r'<(h[12345])[^>]*>(.*?)</\1>', html, re.DOTALL | re.IGNORECASE):
    tag = m.group(1).upper()
    text = unescape(re.sub(r'<.*?>', '', m.group(2))).strip()
    if text:
        print(f"{tag}: {text}")

print('\n=== ALL PDF & DOCUMENT LINKS ===')
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
    href = m.group(1)
    text = unescape(re.sub(r'<.*?>', '', m.group(2))).strip()
    if '.pdf' in href or 'documents' in href or 'topics' in href:
        print(f"  {href} -> {text}")

print('\n=== TIMELINE / CASE EVENTS ===')
timeline_events = re.findall(r'class="timeline-content"[^>]*>(.*?)</div>', html, re.DOTALL)
print(f"Total timeline events: {len(timeline_events)}")
for ev in timeline_events:
    clean_ev = unescape(re.sub(r'<.*?>', ' ', ev)).strip()
    clean_ev = ' '.join(clean_ev.split())
    if clean_ev:
        print(f"  - {clean_ev[:120]}...")
