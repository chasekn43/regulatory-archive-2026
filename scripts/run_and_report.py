import os
import sys
import json
import subprocess
from datetime import datetime

# Note: Proxy routing for HTTP requests is handled by fireprox_config.py 
# which is imported in the child script (run_verification_batch.py).

# Script directory
script_dir = r"c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026"

# Accept brain directory dynamically from command line argument, fallback to current conversation
if len(sys.argv) > 1 and os.path.isabs(sys.argv[1]):
    artifact_dir = sys.argv[1]
else:
    artifact_dir = r"C:\Users\Charwiz43\.gemini\antigravity-ide\brain\8d0e9531-21e6-4a57-a5e1-324d66db741b"
report_filename = "rank_progress_report.md"

def run_sweep():
    print("Running verification sweep...")
    try:
        # Run run_verification_batch.py and stream output in real time
        process = subprocess.Popen(
            [sys.executable, "-u", "run_verification_batch.py"],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )
        
        # Stream stdout in real-time to sys.stdout and flush immediately
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            
        # Stream stderr
        stderr_output = process.stderr.read()
        if stderr_output.strip():
            print("\n--- Subprocess Stderr ---")
            sys.stdout.write(stderr_output)
            sys.stdout.flush()
            
        process.wait()
        print(f"\nSweep complete. Return code: {process.returncode}")
        return process.returncode == 0
    except Exception as e:
        print("Failed to run sweep:", e)
        return False

def generate_report():
    json_path = os.path.join(script_dir, "query_verification_run.json")
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        return
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        timestamp = data.get("timestamp", datetime.now().isoformat())
        engine_summary = data.get("engine_summary", {})
        detailed_results = data.get("detailed_results", {})
        
        # Calculate overall hits
        total_queries = data.get("queries_executed", 0)
        total_hits = sum(stats.get("total_hits", 0) for stats in engine_summary.values())
        
        # Start markdown
        md = []
        md.append(f"# 🔍 GRC Search Indexing & Rank Tracking Report")
        md.append(f"\n> **Last Updated**: {timestamp} (Checked every 15 minutes)")
        md.append(f"> **Target Domain**: `kinslow-regulatory-archive.org`\n")
        
        md.append("## 📊 Engine Performance Summary")
        md.append("| Search Engine | Queries Executed | Avg Latency | Total Results | Target Hits | Hit Rate | Errors |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        
        for engine, stats in engine_summary.items():
            avg_time = round(stats.get("total_time_ms", 0) / stats.get("queries", 1), 2) if stats.get("queries", 0) > 0 else 0
            hit_rate = round((stats.get("total_hits", 0) / stats.get("queries", 1)) * 100, 2) if stats.get("queries", 0) > 0 else 0
            md.append(f"| **{engine}** | {stats.get('queries')} | {avg_time:.1f}ms | {stats.get('total_results')} | {stats.get('total_hits')} | {hit_rate:.1f}% | {stats.get('errors')} |")
            
        md.append(f"\n**Total Target Hits Across All Engines**: `{total_hits}`")
        
        md.append("\n## 🎯 Target Search Results & Keyword Matches")
        md.append("Below are the queries that successfully returned search hits pointing to your public regulatory archive or GitHub repository:")
        
        matches_found = False
        md.append("| Query String | Engine | Matched URL / Title |")
        md.append("| :--- | :--- | :--- |")
        
        for query, engines in detailed_results.items():
            for engine, res in engines.items():
                hit_details = res.get("hit_details", [])
                if hit_details:
                    matches_found = True
                    for hit in hit_details:
                        title = hit.get("title", "No Title")
                        url = hit.get("url", "#")
                        md.append(f"| `{query}` | **{engine}** | [{title}]({url}) |")
                        
        if not matches_found:
            md.append("| *No matches detected in this sweep* | - | - |")
            
        # Write detailed failure check
        md.append("\n## 🛠️ Bot Mitigation & Diagnostics")
        md.append("Monitoring search engine crawl challenges (CAPTCHAs/JS loops):")
        for engine, stats in engine_summary.items():
            status = "🟢 OPERATIONAL"
            if stats.get("errors", 0) > 0:
                status = f"🔴 ERROR ({stats.get('errors')} failures)"
            elif stats.get("total_results", 0) == 0 and engine in ["Google", "Bing"]:
                status = "🟡 BLOCKED (JavaScript Challenge / Redirect)"
            md.append(f"- **{engine}**: {status}")
            
        # Write report to artifact folder
        report_path = os.path.join(artifact_dir, report_filename)
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write("\n".join(md))
        print(f"Progress report generated at {report_path}")
        
        # Write duplicate copy to workspace directory
        workspace_report_path = os.path.join(script_dir, report_filename)
        with open(workspace_report_path, "w", encoding="utf-8") as wf:
            wf.write("\n".join(md))
        print(f"Duplicate workspace copy generated at {workspace_report_path}")
        
    except Exception as e:
        print("Failed to generate report:", e)

if __name__ == "__main__":
    if run_sweep():
        generate_report()
