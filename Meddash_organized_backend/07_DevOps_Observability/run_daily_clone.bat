@echo off
echo === MEDDASH DAILY CLONE (Supabase to SQLite) ===
echo Start: %date% %time%
cd /d "C:\Users\email\.gemini\antigravity\Meddash_organized_backend\07_DevOps_Observability"
python daily_clone.py
echo End: %date% %time%
