import json

def analyze_top():
    with open(r'c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\continuous_search_audit_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    query_summary = {}
    engine_totals = {'Google': 0, 'Bing': 0, 'Yahoo': 0, 'DuckDuckGo': 0}

    for pass_data in data:
        for q_obj in pass_data.get('queries', []):
            q_str = q_obj.get('query')
            hits = q_obj.get('hits', [])

            if q_str not in query_summary:
                query_summary[q_str] = {
                    'runs': 0,
                    'hits_count': 0,
                    'engine_breakdown': {'Google': 0, 'Bing': 0, 'Yahoo': 0, 'DuckDuckGo': 0},
                    'indicators': set(),
                    'urls': set()
                }

            query_summary[q_str]['runs'] += 1

            for hit in hits:
                query_summary[q_str]['hits_count'] += 1
                eng = hit.get('engine')
                ind = hit.get('indicator')
                url = hit.get('url')

                if eng in engine_totals:
                    engine_totals[eng] += 1
                if eng in query_summary[q_str]['engine_breakdown']:
                    query_summary[q_str]['engine_breakdown'][eng] += 1
                if ind:
                    query_summary[q_str]['indicators'].add(ind)
                if url:
                    query_summary[q_str]['urls'].add(url)

    print("================ OVERALL ENGINE TOTAL MATCHES ================")
    for eng, count in engine_totals.items():
        print(f"  {eng:<12}: {count}")

    print("\n================ TOP 15 KEYWORD COMBINATIONS BY TARGET HITS ================")
    sorted_queries = sorted(query_summary.items(), key=lambda x: x[1]['hits_count'], reverse=True)

    for idx, (q_str, stats) in enumerate(sorted_queries[:15], 1):
        print(f"{idx:2d}. Query: \"{q_str}\"")
        print(f"    Total Hits: {stats['hits_count']} across {stats['runs']} run(s)")
        print(f"    Engines: {stats['engine_breakdown']}")
        print(f"    Indicators: {list(stats['indicators'])}")
        print(f"    URLs: {list(stats['urls'])[:2]}\n")

if __name__ == '__main__':
    analyze_top()
