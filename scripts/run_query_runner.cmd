@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Charwiz43\OneDrive\Desktop\SEO ENGINE\regulatory-archive-worker\run_search_query_scheduler.ps1" -IntervalMinutes 15 -QueriesPerRun 200
