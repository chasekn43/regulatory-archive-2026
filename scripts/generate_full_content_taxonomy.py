import glob
import os
import re
import json
from html import unescape

def extract_content():
    files = sorted(glob.glob('topics/*.html')) + ['index.html', 'press-kit.html', 'press-release.html', 'README.md', 'substack_medium_viral_narrative.md']
    
    extracted_taxonomy = []
    
    for f in files:
        if not os.path.exists(f):
            continue
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
            
        t_m = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        title = unescape(re.sub(r'<.*?>', '', t_m.group(1))).strip() if t_m else os.path.basename(f)
        
        # Extract headings
        headings = re.findall(r'<h[1234][^>]*>(.*?)</h[1234]>', content, re.IGNORECASE)
        clean_headings = [unescape(re.sub(r'<.*?>', '', h)).strip() for h in headings if len(h.strip()) > 3]
        
        # Extract strong/bold key concepts
        strongs = re.findall(r'<strong>(.*?)</strong>', content, re.IGNORECASE)
        clean_strongs = [unescape(re.sub(r'<.*?>', '', s)).strip() for s in strongs if 5 < len(s.strip()) < 80]
        
        # Extract specific statutory, case, and factual entities
        statutes = list(set(re.findall(r'(?:12 C\.F\.R\.[^\s<,]+|16 CFR[^\s<,]+|5 U\.S\.C\.[^\s<,]+|UCL \xa7?\s*17200|SOX \d+|CFPB Complaint [0-9-]+|Report \d+-\d+|1LSDCR[A-Z0-9]+)', content)))
        
        extracted_taxonomy.append({
            'file': f,
            'title': title,
            'headings': clean_headings,
            'key_concepts': clean_strongs[:20],
            'statutes_and_ids': statutes
        })
        
    return extracted_taxonomy

if __name__ == '__main__':
    tax = extract_content()
    print(f"Extracted content from {len(tax)} pages/documents.")
    total_h = sum(len(x['headings']) for x in tax)
    total_c = sum(len(x['key_concepts']) for x in tax)
    print(f"Total distinct headings: {total_h}")
    print(f"Total key concepts/takeaways: {total_c}")
    
    # Generate comprehensive query matrix
    all_queries = []
    
    for item in tax:
        # Title queries
        t_clean = re.sub(r'\s*\|\s*.*$', '', item['title'])
        if len(t_clean) > 5:
            all_queries.append(t_clean)
            
        # Heading queries (Real user and research questions/topics)
        for h in item['headings']:
            # Skip generic navigation
            if h.lower() in ['table of contents', 'navigation', 'contact', 'overview', 'summary', 'quick links']:
                continue
            all_queries.append(h)
            
        # Key concept phrases
        for kc in item['key_concepts']:
            if len(kc) > 10:
                all_queries.append(kc)
                
        # Statutes and IDs
        for st in item['statutes_and_ids']:
            all_queries.append(f"Affirm {st}")
            all_queries.append(f"Charles W. Kinslow IV {st}")

    # Remove duplicates preserving order
    seen = set()
    unique_queries = []
    for q in all_queries:
        q_norm = re.sub(r'[^\w\s]', '', q).lower().strip()
        if q_norm not in seen and len(q.split()) >= 2:
            seen.add(q_norm)
            unique_queries.append(q)
            
    print(f"Generated {len(unique_queries)} 100% comprehensive, content-mapped queries across the entire archive.")
    
    with open('comprehensive_archive_taxonomy.json', 'w', encoding='utf-8') as fh:
        json.dump({
            'total_queries': len(unique_queries),
            'taxonomy': tax,
            'queries': unique_queries
        }, fh, indent=2)
        
    with open('keywords_comprehensive.txt', 'w', encoding='utf-8') as fh:
        for q in unique_queries:
            fh.write(q + '\n')
            
    print("Saved to comprehensive_archive_taxonomy.json and keywords_comprehensive.txt.")
