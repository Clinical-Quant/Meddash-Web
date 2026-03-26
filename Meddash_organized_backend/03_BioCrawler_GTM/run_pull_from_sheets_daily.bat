@echo off
echo Starting Meddash Reverse CRM Sync (Google Sheets -^> Local DB)
cd /d "C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM"ized_backend\03_BioCrawler_GTM"
python pull_from_sheets.py
echo Sync Complete. Check crawler_engine\biocrawler_db\biocrawler_leads.db for updates.
