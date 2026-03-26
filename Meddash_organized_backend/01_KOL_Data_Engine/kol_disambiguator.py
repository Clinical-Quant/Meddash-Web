import math
import logging
import argparse
import os
from datetime import datetime
from collections import defaultdict
from itertools import combinations
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

MERGE_THRESHOLD = 0.70
TEMPORAL_WINDOW_YEARS = 10

# Approved signal weights
W_COAUTHOR  = 0.40
W_MESH      = 0.30
W_NAME      = 0.25
W_TEMPORAL  = 0.05

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def ensure_merge_table(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS kol_merge_candidates (
            id SERIAL PRIMARY KEY,
            kol_id_a INTEGER NOT NULL,
            kol_id_b INTEGER NOT NULL,
            score_total REAL NOT NULL,
            score_coauthor REAL DEFAULT 0.0,
            score_mesh REAL DEFAULT 0.0,
            score_name REAL DEFAULT 0.0,
            score_temporal REAL DEFAULT 0.0,
            merge_type VARCHAR(20) DEFAULT 'CANDIDATE',
            status VARCHAR(20) DEFAULT 'PENDING',
            pull_id TEXT,
            detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP WITH TIME ZONE,
            notes TEXT,
            UNIQUE(kol_id_a, kol_id_b)
        );
    """))
    # Ensure pull_id exists if table was created in an older schema version
    conn.execute(text("ALTER TABLE kol_merge_candidates ADD COLUMN IF NOT EXISTS pull_id TEXT;"))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_merge_status ON kol_merge_candidates(status);
        CREATE INDEX IF NOT EXISTS idx_merge_pull_id ON kol_merge_candidates(pull_id);
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS deep_disambiguation_needed (
            id SERIAL PRIMARY KEY,
            kol_id_a INTEGER NOT NULL,
            kol_id_b INTEGER NOT NULL,
            score_total REAL,
            pull_id TEXT,
            gemini_reasoning TEXT,
            escalated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP WITH TIME ZONE,
            resolution TEXT,
            UNIQUE(kol_id_a, kol_id_b)
        );
    """))

def levenshtein(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions    = previous_row[j + 1] + 1
            deletions     = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def score_name(kol_a: dict, kol_b: dict) -> float:
    # Safely handle None values by casting to string before using strip/lower
    last_a = (kol_a.get('last_name') or "").strip().lower()
    last_b = (kol_b.get('last_name') or "").strip().lower()
    if last_a != last_b: return 0.0

    first_a = (kol_a.get('first_name') or "").strip().lower()
    first_b = (kol_b.get('first_name') or "").strip().lower()

    init_a = first_a[0] if first_a else ""
    init_b = first_b[0] if first_b else ""
    initial_score = 0.5 if init_a == init_b else 0.0

    max_len = max(len(first_a), len(first_b), 1)
    dist = levenshtein(first_a, first_b)
    similarity = 1.0 - (dist / max_len)
    fuzzy_score = 0.5 * similarity

    return round(initial_score + fuzzy_score, 4)

def run_disambiguation(pull_id: str = None):
    """
    Scans all KOL pairs inside the sandbox `pull_id` (or globally in `kols` if no pull_id)
    and scores them.
    """
    target_table = "kols_staging" if pull_id else "kols"
    
    with pg_engine.connect() as conn:
        ensure_merge_table(conn)
        conn.commit()
    
        logging.info(f"Targeting environment: {target_table} (pull_id: {pull_id})")

        # Step 1: Handle ORCID auto-merges
        logging.info("Step 1: Checking ORCID-confirmed pairs...")
        if pull_id:
            orcid_query = text(f"""
                SELECT a.id as id_a, b.id as id_b 
                FROM {target_table} a
                JOIN {target_table} b ON a.orcid = b.orcid AND a.id < b.id
                WHERE a.orcid IS NOT NULL AND a.orcid != '' AND :pull = ANY(string_to_array(a.pull_id, ',')) AND :pull = ANY(string_to_array(b.pull_id, ','))
            """)
            orcid_pairs = conn.execute(orcid_query, {"pull": pull_id}).fetchall()
        else:
            orcid_query = text(f"""
                SELECT a.id as id_a, b.id as id_b 
                FROM {target_table} a
                JOIN {target_table} b ON a.orcid = b.orcid AND a.id < b.id
                WHERE a.orcid IS NOT NULL AND a.orcid != ''
            """)
            orcid_pairs = conn.execute(orcid_query).fetchall()

        orcid_merged = 0
        for pair in orcid_pairs:
            try:
                conn.execute(text("""
                    INSERT INTO kol_merge_candidates
                        (kol_id_a, kol_id_b, score_total, merge_type, status, pull_id, notes)
                    VALUES (:a, :b, 1.0, 'ORCID_AUTO', 'APPROVED', :pull, 'Auto-merged: identical ORCID iD')
                    ON CONFLICT DO NOTHING
                """), {"a": pair.id_a, "b": pair.id_b, "pull": pull_id})
                orcid_merged += 1
            except Exception:
                pass
        conn.commit()
        logging.info(f"  ORCID auto-merge candidates flagged: {orcid_merged}")

        # Step 2: Load Co-author, MeSH, Temporal maps
        logging.info("Step 2: Pre-loading data dictionaries...")
        
        ca_query = text("SELECT ka1.kol_id, ka2.kol_id AS coauthor_id FROM kol_authorships ka1 JOIN kol_authorships ka2 ON ka1.publication_id = ka2.publication_id WHERE ka1.kol_id != ka2.kol_id")
        coauthor_map = defaultdict(set)
        for row in conn.execute(ca_query).fetchall():
            coauthor_map[row.kol_id].add(row.coauthor_id)

        mesh_query = text("SELECT ka.kol_id, pmm.mesh_id FROM kol_authorships ka JOIN publications p ON ka.publication_id = p.id JOIN publication_mesh_map pmm ON p.pmid = pmm.pmid")
        mesh_map = defaultdict(set)
        for row in conn.execute(mesh_query).fetchall():
            mesh_map[row.kol_id].add(row.mesh_id)

        temporal_query = text("""
            SELECT ka.kol_id, 
                   MIN(CAST(SUBSTR(CAST(p.published_date AS TEXT), 1, 4) AS INTEGER)) as min_yr,
                   MAX(CAST(SUBSTR(CAST(p.published_date AS TEXT), 1, 4) AS INTEGER)) as max_yr
            FROM kol_authorships ka 
            JOIN publications p ON ka.publication_id = p.id 
            WHERE p.published_date IS NOT NULL AND p.published_date ~ '^[0-9]{4}'
            GROUP BY ka.kol_id
        """)
        temporal_map = {}
        for row in conn.execute(temporal_query).fetchall():
            temporal_map[row.kol_id] = (row.min_yr, row.max_yr)

        # Load KOLs
        if pull_id:
            kol_query = text(f"SELECT id, first_name, last_name, orcid FROM {target_table} WHERE :pull = ANY(string_to_array(pull_id, ',')) ORDER BY last_name, first_name")
            all_kols = [dict(row._mapping) for row in conn.execute(kol_query, {"pull": pull_id}).fetchall()]
        else:
            kol_query = text(f"SELECT id, first_name, last_name, orcid FROM {target_table} ORDER BY last_name, first_name")
            all_kols = [dict(row._mapping) for row in conn.execute(kol_query).fetchall()]

        logging.info(f"  Total KOLs to compare: {len(all_kols)}")

        # Step 3: Probabilistic scoring natively
        logging.info("Step 3: Running probabilistic disambiguation...")
        candidates_added, comparisons_run = 0, 0
        groups = defaultdict(list)
        for kol in all_kols:
            key = (str(kol.get('last_name') or "?")).lower()[0]
            groups[key].append(kol)

        for initial, group in groups.items():
            if len(group) < 2: continue
            for kol_a, kol_b in combinations(group, 2):
                if kol_a.get('orcid') and kol_b.get('orcid') and kol_a['orcid'] != kol_b['orcid']: continue
                comparisons_run += 1
                
                s_name = score_name(kol_a, kol_b)
                if s_name == 0.0: continue

                ca_a = coauthor_map.get(kol_a['id'], set())
                ca_b = coauthor_map.get(kol_b['id'], set())
                s_coauthor = round(len(ca_a & ca_b) / min(len(ca_a), len(ca_b)), 4) if ca_a and ca_b else 0.0

                m_a = mesh_map.get(kol_a['id'], set())
                m_b = mesh_map.get(kol_b['id'], set())
                s_mesh = round(len(m_a & m_b) / len(m_a | m_b), 4) if m_a and m_b else 0.0

                t_a = temporal_map.get(kol_a['id'])
                t_b = temporal_map.get(kol_b['id'])
                if not t_a or not t_b:
                    s_temporal = 0.5
                else:
                    gap = max(t_a[0], t_b[0]) - min(t_a[1], t_b[1])
                    s_temporal = 1.0 if gap <= TEMPORAL_WINDOW_YEARS else 0.0

                composite = (W_COAUTHOR * s_coauthor + W_MESH * s_mesh + W_NAME * s_name + W_TEMPORAL * s_temporal)

                if composite >= MERGE_THRESHOLD:
                    try:
                        conn.execute(text("""
                            INSERT INTO kol_merge_candidates
                                (kol_id_a, kol_id_b, score_total, score_coauthor, score_mesh, score_name, score_temporal, merge_type, status, pull_id)
                            VALUES (:ka, :kb, :st, :sc, :sm, :sn, :stmp, 'CANDIDATE', 'PENDING', :pull)
                            ON CONFLICT DO NOTHING
                        """), {"ka": kol_a['id'], "kb": kol_b['id'], "st": round(composite, 4), 
                                "sc": s_coauthor, "sm": s_mesh, "sn": s_name, "stmp": s_temporal, "pull": pull_id})
                        candidates_added += 1
                    except Exception:
                        pass

        conn.commit()

        logging.info(f"  Comparisons run: {comparisons_run:,}")
        logging.info(f"  Candidate merges added: {candidates_added}")

        # ===== TIER 1: AUTO-VERIFICATION =====
        logging.info("Step 4: Running Tier 1 Auto-Verification...")
        
        # 4a. Auto-merge ORCID-confirmed pairs (score = 1.0)
        orcid_approved = conn.execute(text("""
            SELECT kol_id_a, kol_id_b FROM kol_merge_candidates
            WHERE merge_type = 'ORCID_AUTO' AND status = 'APPROVED' AND pull_id = :pull
        """), {"pull": pull_id}).fetchall() if pull_id else []
        
        merged_count = 0
        for pair in orcid_approved:
            survivor_id, duplicate_id = pair.kol_id_a, pair.kol_id_b
            try:
                # Transfer authorships from duplicate to survivor
                conn.execute(text("UPDATE kol_authorships SET kol_id = :s WHERE kol_id = :d"), {"s": survivor_id, "d": duplicate_id})
                # Mark survivor as verified
                conn.execute(text(f"UPDATE {target_table} SET verification_status = 'verified' WHERE id = :id"), {"id": survivor_id})
                # Delete the duplicate
                conn.execute(text(f"DELETE FROM {target_table} WHERE id = :id"), {"id": duplicate_id})
                # Mark candidate as resolved
                conn.execute(text("UPDATE kol_merge_candidates SET status = 'MERGED' WHERE kol_id_a = :a AND kol_id_b = :b"), {"a": pair.kol_id_a, "b": pair.kol_id_b})
                merged_count += 1
            except Exception as e:
                logging.warning(f"  ORCID merge failed for ({pair.kol_id_a}, {pair.kol_id_b}): {e}")
        conn.commit()
        logging.info(f"  ORCID auto-merged: {merged_count}")
        
        # 4b. Auto-merge high-confidence scored pairs (>= 0.70)
        high_conf = conn.execute(text("""
            SELECT kol_id_a, kol_id_b, score_total FROM kol_merge_candidates
            WHERE merge_type = 'CANDIDATE' AND status = 'PENDING' AND score_total >= 0.70 AND pull_id = :pull
        """), {"pull": pull_id}).fetchall() if pull_id else []
        
        auto_merged = 0
        for pair in high_conf:
            survivor_id, duplicate_id = pair.kol_id_a, pair.kol_id_b
            try:
                conn.execute(text("UPDATE kol_authorships SET kol_id = :s WHERE kol_id = :d"), {"s": survivor_id, "d": duplicate_id})
                conn.execute(text(f"UPDATE {target_table} SET verification_status = 'verified' WHERE id = :id"), {"id": survivor_id})
                conn.execute(text(f"DELETE FROM {target_table} WHERE id = :id"), {"id": duplicate_id})
                conn.execute(text("UPDATE kol_merge_candidates SET status = 'MERGED' WHERE kol_id_a = :a AND kol_id_b = :b"), {"a": pair.kol_id_a, "b": pair.kol_id_b})
                auto_merged += 1
            except Exception as e:
                logging.warning(f"  High-conf merge failed for ({pair.kol_id_a}, {pair.kol_id_b}): {e}")
        conn.commit()
        logging.info(f"  High-confidence auto-merged (>=0.70): {auto_merged}")
        
        # 4c. Auto-verify all standalone KOLs (those NOT involved in any remaining PENDING merge candidates)
        if pull_id:
            standalone_verified = conn.execute(text(f"""
                UPDATE {target_table} SET verification_status = 'verified'
                WHERE :pull = ANY(string_to_array(pull_id, ','))
                AND verification_status = 'pending'
                AND id NOT IN (
                    SELECT kol_id_a FROM kol_merge_candidates WHERE status = 'PENDING' AND pull_id = :pull
                    UNION
                    SELECT kol_id_b FROM kol_merge_candidates WHERE status = 'PENDING' AND pull_id = :pull
                )
            """), {"pull": pull_id})
            conn.commit()
            standalone_count = standalone_verified.rowcount
            logging.info(f"  Standalone KOLs auto-verified: {standalone_count}")
        
        # Summary
        remaining = 0
        if pull_id:
            remaining = conn.execute(text(
                "SELECT COUNT(*) FROM kol_merge_candidates WHERE status = 'PENDING' AND pull_id = :pull"
            ), {"pull": pull_id}).scalar()
        logging.info(f"  Remaining PENDING pairs for HITL review: {remaining}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pull_id", required=False, default=None, help="Campaign Sandbox Pull ID")
    args = parser.parse_args()
    logging.info(f"=== KOL Disambiguation Sandbox Starting (pull_id: {args.pull_id}) ===")
    run_disambiguation(pull_id=args.pull_id)
    logging.info("=== Protocol Complete ===")
