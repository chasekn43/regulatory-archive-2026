"""
Comprehensive Sitemap Generator for Kinslow Regulatory Archive.
Generates complete sitemap with all 83+ public pages, guides, tools, whitepapers, and certified legal exhibits.
"""

import os
import datetime

def generate_sitemap():
    repo_dir = r"c:\Users\Charwiz43\Documents\Chase - Personal\Documents\GitHub\chaseknJD.github.io"
    base_url = "https://kinslow-regulatory-archive.org/"
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    entries = []
    
    # 1. Main Hubs & Root HTML Pages
    for f in sorted(os.listdir(repo_dir)):
        if f.endswith(".html") and not f.startswith("."):
            priority = "1.0" if f == "index.html" else "0.9"
            entries.append((f"{base_url}{f}", priority, "daily" if f in ["index.html", "press-release.html", "press-kit.html"] else "weekly"))
    
    entries.append((f"{base_url}llms.txt", "0.9", "daily"))
    
    # 2. Interactive Tools
    tools_dir = os.path.join(repo_dir, "tools")
    if os.path.exists(tools_dir):
        for f in sorted(os.listdir(tools_dir)):
            if f.endswith(".html"):
                entries.append((f"{base_url}tools/{f}", "0.95", "weekly"))
                
    # 3. Topics (Whitepapers & Deep Dives)
    topics_dir = os.path.join(repo_dir, "topics")
    if os.path.exists(topics_dir):
        for f in sorted(os.listdir(topics_dir)):
            if f.endswith(".html"):
                entries.append((f"{base_url}topics/{f}", "0.9", "weekly"))
                
    # 4. Action Guides
    guides_dir = os.path.join(repo_dir, "guides")
    if os.path.exists(guides_dir):
        for f in sorted(os.listdir(guides_dir)):
            if f.endswith(".html"):
                entries.append((f"{base_url}guides/{f}", "0.9", "weekly"))
                
    # 5. Evidentiary Documents & Primary Source Exhibits
    docs_dir = os.path.join(repo_dir, "documents")
    if os.path.exists(docs_dir):
        for f in sorted(os.listdir(docs_dir)):
            if f.endswith((".pdf", ".md", ".zip", ".json")):
                entries.append((f"{base_url}documents/{f}", "0.85", "monthly"))
                
    # 6. Deep Research Articles
    articles_dir = os.path.join(repo_dir, "articles")
    if os.path.exists(articles_dir):
        for f in sorted(os.listdir(articles_dir)):
            if f.endswith((".md", ".html")):
                entries.append((f"{base_url}articles/{f}", "0.85", "monthly"))
                
    # 7. 7forall / Merchant Return Evidence Dockets
    seven_dir = os.path.join(repo_dir, "7forall")
    if os.path.exists(seven_dir):
        for f in sorted(os.listdir(seven_dir)):
            if f.endswith((".pdf", ".html")):
                entries.append((f"{base_url}7forall/{f}", "0.8", "monthly"))

    # Build XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    
    for url, priority, freq in entries:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{url}</loc>")
        xml_lines.append(f"    <lastmod>{today}</lastmod>")
        xml_lines.append(f"    <changefreq>{freq}</changefreq>")
        xml_lines.append(f"    <priority>{priority}</priority>")
        xml_lines.append("  </url>")
        
    xml_lines.append("</urlset>")
    xml_content = "\n".join(xml_lines)
    
    sitemap_path = os.path.join(repo_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print(f"[OK] Successfully generated comprehensive sitemap with {len(entries)} URLs at: {sitemap_path}")
    return len(entries)

if __name__ == "__main__":
    generate_sitemap()
