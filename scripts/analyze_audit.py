import json
import sys

def analyze():
    # Load continuous_search_report.json
    try:
        with open(r'c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\continuous_search_report.json', 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        print("=== CONTINUOUS SEARCH REPORT OVERVIEW ===")
        print(f"Total passes in report: {len(report_data)}")
    except Exception as e:
        print(f"Error loading report: {e}")
        report_data = []

    # Load continuous_search_audit_results.json
    try:
        with open(r'c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\continuous_search_audit_results.json', 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
        print(f"Total passes in raw audit results: {len(audit_data)}")
    except Exception as e:
        print(f"Error loading raw audit data: {e}")
        audit_data = []

    # Analyze report data
    query_stats = {}
    engine_stats = {'Google': {'success': 0, 'hits': 0}, 'Bing': {'success': 0, 'hits': 0}, 'Yahoo': {'success': 0, 'hits': 0}, 'DuckDuckGo': {'success': 0, 'hits': 0}}

    for pass_item in report_data:
        queries = pass_item.get('queries', [])
        for q_item in queries:
            q_text = q_item.get('query')
            if q_text not in query_stats:
                query_stats[q_text] = {
                    'runs': 0,
                    'engine_hits': {'Google': 0, 'Bing': 0, 'Yahoo': 0, 'DuckDuckGo': 0},
                    'matched_urls': set(),
                    'matched_indicators': set()
                }
            query_stats[q_text]['runs'] += 1
            
            results = q_item.get('results', [])
            for res in results:
                eng = res.get('engine')
                matched_items = res.get('matched_items', [])
                if eng in engine_stats:
                    if res.get('success'):
                        engine_stats[eng]['success'] += 1
                    if len(matched_items) > 0:
                        engine_stats[eng]['hits'] += 1
                        query_stats[q_text]['engine_hits'][eng] += 1

                for mi in matched_items:
                    query_stats[q_text]['matched_indicators'].add(mi.get('indicator'))
                    query_stats[q_text]['matched_urls'].add(mi.get('url'))

    print("\n================ ENGINE SUMMARY (Report Data) ================")
    for eng, st in engine_stats.items():
        print(f"Engine: {eng:<12} | Successful Searches: {st['success']:<4} | Searches with Target Hits: {st['hits']}")

    print("\n================ TOP PERFORMING KEYWORD COMBINATIONS ================")
    sorted_queries = sorted(query_stats.items(), key=lambda x: sum(x[1]['engine_hits'].values()), reverse=True)

    for q_text, stats in sorted_queries:
        total_hits = sum(stats['engine_hits'].values())
        print(f"\nQuery: \"{q_text}\"")
        print(f"  - Total Hits Across Engines: {total_hits}")
        print(f"  - Breakdown by Engine: {stats['engine_hits']}")
        print(f"  - Indicators Matched: {list(stats['matched_indicators'])}")
        print(f"  - Target URLs Found ({len(stats['matched_urls'])}):")
        for url in list(stats['matched_urls'])[:5]:
            print(f"      * {url}")

    # Also inspect search_continuous.log summary
    print("\n================ READING LOG FILE HIGHLIGHTS ================")
    try:
        with open(r'c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\search_continuous.log', 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        print(f"Total lines in log: {len(log_lines)}")
        matching_log_lines = [l.strip() for l in log_lines if "[MATCH]" in l or "Target found" in l or "PASS" in l or "Summary" in l]
        print(f"Total MATCH / Summary lines found in log: {len(matching_log_lines)}")
        for l in matching_log_lines[:20]:
            print(f"  {l}")
    except Exception as e:
        print(f"Error reading log file: {e}")

if __name__ == '__main__':
    analyze()
