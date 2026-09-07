"""
Comprehensive Site Visibility, Perplexity Citation & SERP Audit Runner.
"""

import os
import json
import time
from perplexity_search import PerplexitySearchClient

def run_citation_audit():
    print("=" * 60)
    print("1. RUNNING PERPLEXITY AI CITATION & SERP AUDIT")
    print("=" * 60)

    client = PerplexitySearchClient()
    
    target_queries = [
        "kinslow regulatory archive",
        "Affirm dispute letter template 12 CFR 1026.13",
        "CFPB Buy Now Pay Later interpretive rule digital accounts",
        "Affirm return refund merchant dispute rights",
        "Buy Now Pay Later billing error dispute procedures",
        "12 CFR 1026.13 fintech dispute notice requirements",
        "Affirm customer service phone bypass"
    ]

    audit_summary = []
    domain_target = "kinslow-regulatory-archive.org"

    for query in target_queries:
        try:
            resp = client.search(query=query, max_results=5, country="US")
            found_domain = False
            top_ranked = []
            for rank, item in enumerate(resp.results, 1):
                is_archive = domain_target in item.url.lower()
                if is_archive:
                    found_domain = True
                top_ranked.append({
                    "rank": rank,
                    "title": item.title,
                    "url": item.url,
                    "is_archive": is_archive,
                    "date": item.date,
                    "snippet": item.snippet[:200]
                })

            audit_summary.append({
                "query": query,
                "domain_ranked": found_domain,
                "top_results": top_ranked
            })
            print(f"[OK] Audited query: '{query}' | Total results: {len(resp.results)} | Archive cited: {found_domain}")
            time.sleep(0.5)

        except Exception as err:
            print(f"[!] Error querying '{query}': {err}")

    with open("perplexity_citation_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)

    print("\nSaved full audit data to perplexity_citation_audit.json")
    return audit_summary

if __name__ == "__main__":
    run_citation_audit()
