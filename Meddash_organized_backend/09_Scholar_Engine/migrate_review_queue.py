import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('C:/Users/email/.gemini/antigravity/Meddash_organized_backend/.env')
engine = create_engine(os.getenv('SUPABASE_URI'))

sql = """
CREATE TABLE IF NOT EXISTS public.scholar_review_queue (
    id SERIAL PRIMARY KEY,
    kol_id TEXT NOT NULL,
    kol_name TEXT NOT NULL,
    candidate_scholar_id TEXT NOT NULL,
    candidate_name TEXT,
    candidate_affiliation TEXT,
    candidate_interests TEXT,
    disambiguation_tier_failed TEXT,
    confidence_score INTEGER DEFAULT 0,
    reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_queue_reviewed 
ON public.scholar_review_queue(reviewed);
"""

try:
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("SUCCESS: scholar_review_queue table provisioned in Supabase!")
except Exception as e:
    print(f"FAILED: {e}")
