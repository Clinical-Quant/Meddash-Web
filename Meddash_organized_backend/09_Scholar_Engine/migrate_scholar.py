import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load the core Meddash environment variables
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

SUPABASE_URI = os.getenv("SUPABASE_URI")

if not SUPABASE_URI:
    print("FATAL: Could not locate SUPABASE_URI in .env")
    exit(1)

engine = create_engine(SUPABASE_URI)

sql = """
CREATE TABLE IF NOT EXISTS public.kol_scholar_metrics (
    kol_id TEXT PRIMARY KEY,
    scholar_id TEXT NOT NULL UNIQUE,
    total_citations INTEGER DEFAULT 0,
    h_index INTEGER DEFAULT 0,
    i10_index INTEGER DEFAULT 0,
    last_updated_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scholar_metrics_updated 
ON public.kol_scholar_metrics(last_updated_date);
"""

try:
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("SUCCESS: Provisioned kol_scholar_metrics table directly to Supabase via API bridge!")
except Exception as e:
    print(f"FAILED to execute SQL schema on Supabase: {e}")
