import os
import sys
import json
import time
from datetime import datetime

# Import functions from multi_engine_search_suite
sys.path.insert(0, os.path.dirname(__file__))
from multi_engine_search_suite import (
    search_duckduckgo,
    search_google,
    search_bing,
    search_yahoo,
    is_target_match
)

QUERIES_SET_B = [
    "Chase Kinslow Fintech BNPL merchant dispute",
    "Chase Kinslow CFPB Administrative Procedures Act",
    "Chase Kinslow customer service refund delays",
    "Chase Kinslow point of sale lines of credit",
    "Chase Kinslow Affirm Morgan Lewis Bockius lawsuit",
    "Chase Kinslow Andy Chen Affirm cease and desist",
    "Chase Kinslow Madison Marshall Arjun Rao Morgan Lewis",
    "Chase Kinslow Scott Williams Affirm Vice President Client Success",
    "Chase Kinslow Affirm in-app payment lock BillPay workaround"
]

def run_batch_b():
    print("Starting Multi-Engine Search Execution for Query Set B...")
    results = {
        "timestamp": datetime.now().isoformat(),
        "query_set": "Set B - Corporate & Outside Counsel",
        "queries": []
    }

    for idx, q in enumerate(QUERIES_SET_B, 1):
        print(f"\n[{idx}/{len(QUERIES_SET_B)}] Executing search for query: '{q}'")
        q_entry = {
            "query": q,
            "engines": {},
            "counts": {},
            "target_matches": []
        }

        # 1. DuckDuckGo
        ddg = search_duckduckgo(q)
        q_entry["engines"]["DuckDuckGo"] = ddg
        q_entry["counts"]["DuckDuckGo"] = len([r for r in ddg if "error" not in r])

        time.sleep(1)

        # 2. Google
        goog = search_google(q)
        q_entry["engines"]["Google"] = goog
        q_entry["counts"]["Google"] = len([r for r in goog if "error" not in r])

        time.sleep(1)

        # 3. Bing
        bing = search_bing(q)
        q_entry["engines"]["Bing"] = bing
        q_entry["counts"]["Bing"] = len([r for r in bing if "error" not in r])

        time.sleep(1)

        # 4. Yahoo
        yahoo = search_yahoo(q)
        q_entry["engines"]["Yahoo"] = yahoo
        q_entry["counts"]["Yahoo"] = len([r for r in yahoo if "error" not in r])

        # Find target matches across engines
        matches = []
        for eng_name, items in q_entry["engines"].items():
            for item in items:
                if "url" in item:
                    matched, ind = is_target_match(item.get("url", ""), item.get("title", ""), item.get("snippet", ""))
                    if matched:
                        matches.append({
                            "engine": eng_name,
                            "indicator": ind,
                            "title": item.get("title"),
                            "url": item.get("url")
                        })
        q_entry["target_matches"] = matches

        results["queries"].append(q_entry)
        time.sleep(1.5)

    output_path = os.path.join(os.path.dirname(__file__), "batch_b_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nExecution finished. Data saved to {output_path}")

if __name__ == "__main__":
    run_batch_b()
