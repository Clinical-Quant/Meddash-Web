import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv('C:/Users/email/.gemini/antigravity/Meddash_organized_backend/.env')
uri = os.getenv('SUPABASE_URI')
engine = create_engine(uri)
inspector = inspect(engine)

for t in ['trials', 'biotech_leads']:
    if t in inspector.get_table_names():
        print(f"--- {t} ---")
        for c in inspector.get_columns(t):
            print(c['name'])
