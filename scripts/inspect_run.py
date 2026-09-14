import json

with open("query_verification_run.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Bing parsed results:")
for query, engines in data["detailed_results"].items():
    bing_res = engines["Bing"].get("raw_results", [])
    print(f"\nQuery: '{query}' -> parsed {len(bing_res)} results:")
    for idx, res in enumerate(bing_res[:3]):
        print(f"  {idx+1}. Title: {res.get('title')} | URL: {res.get('url')[:80]}")
