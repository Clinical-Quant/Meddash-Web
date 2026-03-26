import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
load_dotenv('C:/Users/email/.gemini/antigravity/Meddash_organized_backend/.env')
uri = os.getenv('SUPABASE_URI')
engine = create_engine(uri)
columns = inspect(engine).get_columns('kols')
print("KOLS:", [c['name'] for c in columns])
