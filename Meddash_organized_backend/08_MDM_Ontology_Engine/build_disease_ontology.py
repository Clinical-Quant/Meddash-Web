import os
import sys
import psycopg2
from dotenv import load_dotenv

# Mount dotEnv specifically targeting the parent directory to keep universal constants
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))

DB_URI = os.getenv("SUPABASE_URI")
UMLS_KEY = os.getenv("UMLS_API_KEY")

class MDM_Ontology_Engine:
    def __init__(self):
        if not DB_URI:
            print("FATAL: SUPABASE_URI missing from .env")
            sys.exit(1)
        
        try:
            self.conn = psycopg2.connect(DB_URI)
            self.cur = self.conn.cursor()
            print("Connected securely to PostgreSQL Master Database Cluster.")
        except Exception as e:
            print(f"FATAL: Database connectivity failed -> {e}")
            sys.exit(1)

    def provision_schema(self):
        print("Provisioning Global Disease Criteria Ontology Tables...")
        
        queries = [
            '''
            CREATE TABLE IF NOT EXISTS ontology_mesh (
                mesh_id VARCHAR(50) PRIMARY KEY,
                term VARCHAR(255) NOT NULL,
                tree_numbers TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS ontology_icd10 (
                icd_code VARCHAR(50) PRIMARY KEY,
                description TEXT NOT NULL,
                chapter VARCHAR(255),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS ontology_snomed (
                concept_id VARCHAR(100) PRIMARY KEY,
                fully_specified_name TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS ontology_crosswalk (
                id SERIAL PRIMARY KEY,
                mesh_id VARCHAR(50) REFERENCES ontology_mesh(mesh_id) ON DELETE CASCADE,
                icd_code VARCHAR(50) REFERENCES ontology_icd10(icd_code) ON DELETE CASCADE,
                snomed_concept_id VARCHAR(100) REFERENCES ontology_snomed(concept_id) ON DELETE CASCADE,
                confidence_score FLOAT DEFAULT 1.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS system_changelog (
                log_id SERIAL PRIMARY KEY,
                script_name VARCHAR(255) NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            '''
        ]
        
        for q in queries:
            try:
                self.cur.execute(q)
            except Exception as e:
                print(f"Warning: Error executing schema check: {e}")
                
        self.conn.commit()
        print("Schema verification complete.")
        
        # Log the schema update natively into the changelog
        self.cur.execute("INSERT INTO system_changelog (script_name, action_type, details) VALUES (%s, %s, %s)", 
                         ("build_disease_ontology.py", "SCHEMA_INIT", "Provisioned Relational MeSH/ICD10/SNOMED schema tracking layers."))
        self.conn.commit()

    def sync_umls_api(self):
        if not UMLS_KEY or UMLS_KEY == "YOUR_NIH_UMLS_KEY_HERE":
            print("\n========================================================")
            print("\u26d4 NIH UMLS SYNC PAUSED \u26d4")
            print("You must register for a free UMLS API Key from the National Library of Medicine:")
            print("https://uts.nlm.nih.gov/uts/signup-login")
            print("Once approved, add it to your .env file as UMLS_API_KEY='key'.")
            print("For now, the Phase 5 database tables have been successfully structurally provisioned in PostgreSQL!")
            print("========================================================\n")
            return
            
        print("Initiating active UMLS Sync Sequence...")
        # To be implemented by CEO once key is acquired.

    def run(self):
        self.provision_schema()
        self.sync_umls_api()

if __name__ == "__main__":
    engine = MDM_Ontology_Engine()
    engine.run()
