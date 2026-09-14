import json

with open('live_indexation_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

hits_found = 0
for q, engines in data.items():
    query_hits = []
    for eng, res in engines.items():
        if isinstance(res, list):
            for r in res:
                if isinstance(r, dict) and r.get('is_target'):
                    query_hits.append((eng, r.get('rank'), r.get('title'), r.get('url')))
    if query_hits:
        hits_found += 1
        print(f"\nQuery: \"{q}\"")
        for eng, rank, title, url in query_hits:
            print(f"  - [{eng}] Rank #{rank}: {title} -> {url}")

print(f"\nTotal queries with target hits: {hits_found} / {len(data)}")
