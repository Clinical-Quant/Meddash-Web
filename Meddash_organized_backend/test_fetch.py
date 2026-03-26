import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('C:/Users/email/.gemini/antigravity/Meddash_organized_backend/.env')
engine = create_engine(os.getenv('SUPABASE_URI'))

with engine.connect() as conn:
    res = conn.execute(text("SELECT id FROM kols LIMIT 1")).fetchone()
    if res:
        kol_id = res[0]
        print(f"Test KOL ID: {kol_id}")
        os.system(f"python C:/Users/email/.gemini/antigravity/Meddash_organized_backend/09_Scholar_Engine/sync_scholar_citations.py --kol_id {kol_id}")
    else:
        print("No KOLs found!")
