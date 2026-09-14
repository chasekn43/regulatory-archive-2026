import json

def analyze_full_raw():
    with open(r'c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\continuous_search_audit_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total Audit Runs/Passes recorded in JSON: {len(data)}")

    query_summary = {}
    engine_summary = {'Google': 0, 'Bing': 0, 'Yahoo': 0, 'DuckDuckGo': 0}
    total_query_runs = 0

    for pass_data in data:
        pass_num = pass_data.get('pass_number')
        timestamp = pass_data.get('timestamp')
        queries = pass_data.get('queries', [])

        for q_obj in queries:
            q_str = q_obj.get('query')
            hits = q_obj.get('hits', [])
            engines = q_obj.get('engines', {})

            if q_str not in query_summary:
                query_summary[q_str] = {
                    'times_tested': 0,
                    'hits_count': 0,
                    'engine_breakdown': {'Google': 0, 'Bing': 0, 'Yahoo': 0, 'DuckDuckGo': 0},
                    'matched_indicators': set(),
                    'urls': set()
                }

            query_summary[q_str]['times_tested'] += 1
            total_query_runs += 1

            for hit in hits:
                query_summary[q_str]['hits_count'] += 1
                eng = hit.get('engine')
                ind = hit.get('indicator')
                url = hit.get('url')

                if eng in engine_summary:
                    engine_summary[eng] += 1
                if eng in query_summary[q_str]['engine_breakdown']:
                    query_summary[q_str]['engine_breakdown'][eng] += 1
                if ind:
                    query_summary[q_str]['matched_indicators'].add(ind)
                if url:
                    query_summary[q_str]['urls'].add(url)

    print("\n================ TOTAL MATCHES BY SEARCH ENGINE (ALL PASSES) ================")
    for eng, count in engine_summary.items():
        print(f"  {eng:<12}: {count} total target indicator hits")

    print("\n================ DETAILED QUERY RANKINGS & MATCH METRICS ================")
    sorted_queries = sorted(query_summary.items(), key=lambda x: x[1]['hits_count'], reverse=True)

    for idx, (q_str, stats) in enumerate(sorted_queries, 1):
        print(f"\n[{idx}] Query: \"{q_str}\"")
        print(f"    - Executed: {stats['times_tested']} time(s)")
        print(f"    - Total Target Hits: {stats['hits_count']}")
        print(f"    - Engine Distribution: {stats['engine_breakdown']}")
        print(f"    - Indicators Triggered: {list(stats['matched_indicators'])}")
        print(f"    - Sample URLs Matched:")
        for u in list(stats['urls'])[:3]:
            print(f"        * {u}")

if __name__ == '__main__':
    analyze_full_raw()
