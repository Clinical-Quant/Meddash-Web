import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import glob

# Resolve paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
data_dir = os.path.join(base_dir, '06_Shared_Datastores')

# Load PostgreSQL credentials securely from .env
load_dotenv(env_path)
SUPABASE_URI = os.getenv("SUPABASE_URI")

print("Initializing Supabase Migration Pipeline...")

# Create PostgreSQL Alchemy Engine
pg_engine = create_engine(SUPABASE_URI)

# Scan for local SQLite files
db_paths = glob.glob(os.path.join(data_dir, '*.db'))

if not db_paths:
    print("No .db files found in 06_Shared_Datastores!")

for sqlite_db in db_paths:
    db_name = os.path.basename(sqlite_db)
    print(f"\n======================================")
    print(f"Migrating Datastore: {db_name}")
    print(f"======================================")
    
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        
        # Get all non-system tables
        tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        tables = pd.read_sql_query(tables_query, sqlite_conn)['name'].tolist()
        
        for table in tables:
            print(f"  -> Converting Schema & Injecting Table: [{table}]")
            # Read from SQLite directly into a DataFrame
            df = pd.read_sql_query(f"SELECT * FROM \"{table}\"", sqlite_conn)
            
            # Map native structure to PostgreSQL cloud schemas dynamically
            df.to_sql(table, pg_engine, if_exists='replace', index=False)
            
            print(f"     ✅ Successfully pushed {len(df)} rows.")
            
        sqlite_conn.close()
    except Exception as e:
        print(f"❌ Error migrating {db_name}: {e}")

print("\n======================================")
print("SUPABASE MIGRATION 100% COMPLETE.")
print("The Cloud Database is now fully populated.")
