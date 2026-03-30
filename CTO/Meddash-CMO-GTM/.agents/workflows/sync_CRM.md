---
description: Synchronizes the Google Sheets CRM with the local BioCrawler Database.
---

# Sync CRM

This workflow automatically pulls your manual GTM work from your Google Spreadsheet and seamlessly pushes any new AI-generated leads straight to the cloud.

1. Always navigate explicitly to the backend CRM engine directory: `c:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM`.
// turbo-all
2. Run the inbound syncer using `python pull_from_sheets.py` to capture any missing websites or manual spreadsheet edits you made, saving them into your SQLite database.
3. Immediately afterwards, run the outbound exporter using `python push_to_sheets.py` to blast the top 20 newest machine-generated leads up to your Google Sheet.
4. Provide a clear summary reading the terminal logs to the user to tell them exactly how many leads were synced in both directions.
