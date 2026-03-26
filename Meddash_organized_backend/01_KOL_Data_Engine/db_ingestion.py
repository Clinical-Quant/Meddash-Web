import os
import json
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Resolve paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')

load_dotenv(env_path)
SUPABASE_URI = os.getenv("SUPABASE_URI")

if not SUPABASE_URI:
    print("FATAL: Missing SUPABASE_URI in .env")
    exit(1)

pg_engine = create_engine(SUPABASE_URI)

def initialize_database():
    """
    Supabase schemas already exist for publications, etc.
    We rely on the pre-provisioned PostgreSQL cloud schemas.
    """
    pass

def ingest_publications_from_json(json_filepath: str, pull_id: str = None):
    """
    Reads a JSON file of extracted publications and inserts them into PostgreSQL.
    If pull_id is provided, KOLs go securely into kols_staging first.
    """
    print(f"\nReading extracted data from {json_filepath} (Pull ID: {pull_id})...")
    if not os.path.exists(json_filepath):
        print("Error: JSON file not found. Please run the extraction script first.")
        return

    with open(json_filepath, 'r') as f:
        publications_data = json.load(f)

    print(f"Loaded {len(publications_data)} publications to ingest.")

    new_pubs_added = 0
    kols_processed = 0
    mesh_processed = 0

    with pg_engine.connect() as conn:
        for pub in publications_data:
            trans = conn.begin()
            try:
                # 1. Check if Publication exists
                pub_res = conn.execute(text("SELECT id FROM publications WHERE pmid = :pmid"), {"pmid": pub.get('pmid')}).fetchone()
                
                if pub_res:
                    db_pub_id = pub_res[0]
                    conn.execute(text("""
                        UPDATE publications SET 
                            abstract = :abstract, 
                            url = :url, 
                            issn = :issn, 
                            journal_name = :journal_name
                        WHERE id = :id;
                    """), {
                        "abstract": pub.get('abstract'),         
                        "url": pub.get('url'),              
                        "issn": pub.get('issn'),
                        "journal_name": pub.get('journal'),
                        "id": db_pub_id
                    })
                else:
                    conn.execute(text("""
                        INSERT INTO publications 
                        (pmid, doi, title, journal_name, published_date, publication_type, abstract, url, issn)
                        VALUES (:pmid, :doi, :title, :journal_name, :published_date, :type, :abstract, :url, :issn)
                    """), {
                        "pmid": pub.get('pmid'),
                        "doi": pub.get('doi'),
                        "title": pub.get('title'),
                        "journal_name": pub.get('journal'),
                        "published_date": pub.get('published_date'),
                        "type": pub.get('publication_type'),
                        "abstract": pub.get('abstract'),         
                        "url": pub.get('url'),              
                        "issn": pub.get('issn')              
                    })
                
                # Fetch pub_id
                res = conn.execute(text("SELECT id FROM publications WHERE pmid = :pmid"), {"pmid": pub.get('pmid')}).fetchone()
                if not res and pub.get('doi'):
                    res = conn.execute(text("SELECT id FROM publications WHERE doi = :doi"), {"doi": pub.get('doi')}).fetchone()
                
                if not res:
                    print(f"Warning: Could not resolve publication ID for PMID {pub.get('pmid')}. Skipping authors.")
                    trans.rollback()
                    continue
                    
                db_pub_id = res[0]

                # 2. Process Authors
                for author in pub.get('authors', []):
                    name_parts = author['name'].split(' ', 1)
                    fore_name = name_parts[0] if len(name_parts) > 0 else "Unknown"
                    last_name = name_parts[1] if len(name_parts) > 1 else author['name']
                    orcid = author.get('orcid')  
                    affiliation = author.get('affiliation')  

                    kol_record = None
                    
                    # Check target table: kols or kols_staging
                    target_table = "kols_staging" if pull_id else "kols"

                    if orcid:
                        kol_record = conn.execute(text(f"""
                            SELECT id, pull_id FROM {target_table}
                            WHERE orcid = :orcid LIMIT 1
                        """), {"orcid": orcid}).fetchone()
                    else:
                        kol_record = conn.execute(text(f"""
                            SELECT id, pull_id FROM {target_table}
                            WHERE first_name = :first AND last_name = :last LIMIT 1
                        """), {"first": fore_name, "last": last_name}).fetchone()

                    if not kol_record:
                        if pull_id:
                            res = conn.execute(text(f"""
                                INSERT INTO {target_table} (first_name, last_name, orcid, institution, pull_id)
                                VALUES (:first, :last, :orcid, :inst, :pull) RETURNING id;
                            """), {"first": fore_name, "last": last_name, "orcid": orcid, "inst": affiliation, "pull": pull_id}).fetchone()
                        else:
                            res = conn.execute(text(f"""
                                INSERT INTO {target_table} (first_name, last_name, orcid, institution)
                                VALUES (:first, :last, :orcid, :inst) RETURNING id;
                            """), {"first": fore_name, "last": last_name, "orcid": orcid, "inst": affiliation}).fetchone()
                        
                        # Get the inserted ID natively
                        db_kol_id = res[0]
                    else:
                        db_kol_id = kol_record[0]
                        existing_pulls = kol_record[1] if kol_record[1] else ""
                        
                        # Append the pull_id if it's new
                        if pull_id and pull_id not in existing_pulls.split(","):
                            new_pulls = f"{existing_pulls},{pull_id}" if existing_pulls else pull_id
                            conn.execute(text(f"UPDATE {target_table} SET pull_id = :p WHERE id = :id"), {"p": new_pulls, "id": db_kol_id})
                            
                        if orcid:
                            conn.execute(text(f"UPDATE {target_table} SET orcid = :o WHERE id = :id AND orcid IS NULL"), {"o": orcid, "id": db_kol_id})
                        if affiliation:
                            conn.execute(text(f"UPDATE {target_table} SET institution = :i WHERE id = :id AND (institution IS NULL OR institution = '')"), {"i": affiliation, "id": db_kol_id})
                        
                    kols_processed += 1

                    is_primary_int = 1 if author['is_primary'] else 0
                    
                    try:
                        with conn.begin_nested():
                            auth_res = conn.execute(text("SELECT kol_id FROM kol_authorships WHERE kol_id = :kid AND publication_id = :pid"), {"kid": db_kol_id, "pid": db_pub_id}).fetchone()
                            if not auth_res:
                                conn.execute(text("""
                                    INSERT INTO kol_authorships 
                                    (kol_id, publication_id, is_primary_author, author_position)
                                    VALUES (:kid, :pid, :prim, :pos);
                                """), {"kid": db_kol_id, "pid": db_pub_id, "prim": is_primary_int, "pos": author['position']})
                    except Exception as e:
                        print(f"Skipping authorship conflict: {e}")

                # 3. Process MeSH Terms
                for mesh in pub.get('mesh_terms', []):
                    mesh_id = mesh.get('mesh_id')
                    mesh_term = mesh.get('mesh_term')
                    is_major = 1 if mesh.get('is_major_topic') else 0
                    
                    try:
                        with conn.begin_nested():
                            mesh_res = conn.execute(text("SELECT mesh_id FROM mesh_ontology WHERE mesh_id = :id"), {"id": mesh_id}).fetchone()
                            if not mesh_res:
                                conn.execute(text("""
                                    INSERT INTO mesh_ontology (mesh_id, mesh_term)
                                    VALUES (:id, :term);
                                """), {"id": mesh_id, "term": mesh_term})
                    except Exception as e:
                        print(f"Skipping mesh insert error: {e}")
                    
                    try:
                        with conn.begin_nested():
                            pmm_res = conn.execute(text("SELECT pmid FROM publication_mesh_map WHERE pmid = :pmid AND mesh_id = :mid"), {"pmid": pub.get('pmid'), "mid": mesh_id}).fetchone()
                            if not pmm_res:
                                conn.execute(text("""
                                    INSERT INTO publication_mesh_map (pmid, mesh_id, is_major_topic)
                                    VALUES (:pmid, :mid, :maj);
                                """), {"pmid": pub.get('pmid'), "mid": mesh_id, "maj": is_major})
                    except Exception as e:
                        print(f"Skipping map insert error: {e}")
                    
                    mesh_processed += 1
                    
                trans.commit()
                new_pubs_added += 1
                
            except Exception as e:
                print(f"Error processing publication {pub.get('pmid')}: {e}")
                trans.rollback()

    print(f"Ingestion complete! Added {new_pubs_added} publications to DB, {kols_processed} authorship records, and {mesh_processed} MeSH mappings.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to JSON file")
    parser.add_argument("--pull_id", required=False, help="Campaign Sandbox Pull ID", default=None)
    args = parser.parse_args()
    
    ingest_publications_from_json(args.json, pull_id=args.pull_id)
