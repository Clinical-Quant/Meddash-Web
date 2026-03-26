import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('C:/Users/email/.gemini/antigravity/Meddash_organized_backend/.env')
engine = create_engine(os.getenv('SUPABASE_URI'))

sql_statements = [
    # 1. Add pull_id to main kols table if it doesn't exist
    """
    ALTER TABLE public.kols 
    ADD COLUMN IF NOT EXISTS pull_id TEXT;
    """,
    # 2. Create the kols_staging table
    """
    CREATE TABLE IF NOT EXISTS public.kols_staging (
        id SERIAL PRIMARY KEY,
        pull_id TEXT NOT NULL,
        verification_status TEXT DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
        first_name TEXT,
        last_name TEXT,
        degree TEXT,
        institution TEXT,
        specialty TEXT,
        orcid TEXT,
        author_publication_weight REAL DEFAULT 0.0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 3. Create indices for faster sandbox grouping queries
    """
    CREATE INDEX IF NOT EXISTS idx_kols_staging_pull_id ON public.kols_staging(pull_id);
    """
]

try:
    with engine.connect() as conn:
        for stmt in sql_statements:
            conn.execute(text(stmt))
        conn.commit()
    print("SUCCESS: Campaign Sandbox (Pull ID) Schema Migrations completed!")
except Exception as e:
    print(f"FAILED: {e}")
