@echo off
REM BioCrawler Daily Execution Script
REM This script is designed to be triggered by Windows Task Scheduler every day at 5:00 PM.

cd /d "c:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM"

echo ==========================================================
echo Starting BioCrawler Execution: %date% %time%
echo ==========================================================

python biocrawler.py

echo ==========================================================
echo Execution Complete: %date% %time%
echo ==========================================================

REM Append log to a file
echo [%date% %time%] BioCrawler completed successfully. >> biocrawler_cron.log
