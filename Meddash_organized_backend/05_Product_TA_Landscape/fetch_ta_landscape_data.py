import os
import sqlite3
import json
import argparse
import urllib.parse
import urllib.request
import time
from Bio import Entrez
import xml.etree.ElementTree as ET

# Configure Entrez
Entrez.email = 'YOUR_EMAIL@example.com'  # User should replace this if deployed, but for local it's fine

# Database Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CT_DB_PATH = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
KOL_DB_PATH = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"
BIOCRAWLER_DB_PATH = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db"

# Cache Directory
CACHE_DIR = os.path.join(BASE_DIR, 'ta_landscape_cache')

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def fetch_pubmed_abstracts(query, max_results=10):
    """Fetches PubMed abstracts for disease overview & mechanisms."""
    print(f"[*] Fetching up to {max_results} PubMed articles for query: {query}")
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        
        pmids = record["IdList"]
        if not pmids:
            return []
            
        handle = Entrez.efetch(db="pubmed", id=",".join(pmids), retmode="xml")
        xml_data = handle.read()
        handle.close()
        
        root = ET.fromstring(xml_data)
        articles = []
        for article in root.findall('.//PubmedArticle'):
            pmid = article.find('.//PMID').text
            title = article.find('.//ArticleTitle')
            title_text = title.text if title is not None else "No Title"
            
            abstract_texts = article.findall('.//AbstractText')
            abstract_text = " ".join([elem.text for elem in abstract_texts if elem.text])
            
            pub_date = article.find('.//PubDate/Year')
            year = pub_date.text if pub_date is not None else "Unknown"

            if abstract_text:
                articles.append({
                    "pmid": pmid,
                    "title": title_text,
                    "year": year,
                    "abstract": abstract_text
                })
        return articles
    except Exception as e:
        print(f"[!] Error fetching PubMed data: {e}")
        return []

def query_internal_db(db_path, query, params=(), label=""):
    """Executes a query against an internal Meddash SQLite database."""
    print(f"[*] Querying internal db '{os.path.basename(db_path)}' for {label}...")
    if not os.path.exists(db_path):
        print(f"   [!] DB not found: {db_path}")
        return []
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(query, params)
        results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"   [!] Error executing {label} query: {e}")
        return []

def fetch_trial_landscape(disease_term):
    """Extracts trial geographic, sponsor, and intervention aggregates."""
    # We use a LIKE match on conditions to find relevant NCT IDs
    condition_query = "%" + disease_term + "%"
    
    # 1. Trial Geography
    geo_query = """
    SELECT country, city, COUNT(DISTINCT nct_id) as trials 
    FROM trial_sites 
    WHERE nct_id IN (SELECT nct_id FROM trial_conditions WHERE condition LIKE ?)
    GROUP BY country, city
    ORDER BY trials DESC
    LIMIT 20;
    """
    geography = query_internal_db(CT_DB_PATH, geo_query, (condition_query,), "Geographic Footprint")

    # 2. Sponsor Landscape
    sponsor_query = """
    SELECT sponsor_name as lead_sponsor_name, COUNT(DISTINCT nct_id) as trials 
    FROM trial_sponsors 
    WHERE role = 'PRINCIPAL_INVESTIGATOR' OR is_lead = 1
      AND nct_id IN (SELECT nct_id FROM trial_conditions WHERE condition LIKE ?)
    GROUP BY sponsor_name
    ORDER BY trials DESC
    LIMIT 15;
    """
    sponsors = query_internal_db(CT_DB_PATH, sponsor_query, (condition_query,), "Sponsor Landscape")

    # 3. Leading Interventions
    intervention_query = """
    SELECT intervention_name, intervention_type, COUNT(DISTINCT nct_id) as trials 
    FROM trial_interventions 
    WHERE nct_id IN (SELECT nct_id FROM trial_conditions WHERE condition LIKE ?)
    GROUP BY intervention_name, intervention_type
    ORDER BY trials DESC
    LIMIT 15;
    """
    interventions = query_internal_db(CT_DB_PATH, intervention_query, (condition_query,), "Interventions")

    # 4. Leading Phase 3 Trials (Catalysts)
    catalysts_query = """
    SELECT nct_id, brief_title as study_title, phase, primary_completion_date 
    FROM trials 
    WHERE phase LIKE '%Phase 3%' 
      AND nct_id IN (SELECT nct_id FROM trial_conditions WHERE condition LIKE ?)
      AND primary_completion_date >= date('now')
    ORDER BY primary_completion_date
    LIMIT 10;
    """
    catalysts = query_internal_db(CT_DB_PATH, catalysts_query, (condition_query,), "Phase 3 Catalysts")

    return {
        "geography": geography,
        "sponsors": sponsors,
        "interventions": interventions,
        "catalysts": catalysts
    }

def fetch_biocrawler_catalysts(sponsor_list):
    """Checks the BioCrawler database for funding or catalyst events for the top sponsors."""
    if not sponsor_list:
        return []
    
    sponsor_names = [s['lead_sponsor_name'] for s in sponsor_list]
    placeholders = ",".join(["?"] * len(sponsor_names))
    
    query = f"""
    SELECT company_name, funding_stage, tags, estimated_headcount, url 
    FROM biotech_companies 
    WHERE company_name IN ({placeholders});
    """
    return query_internal_db(BIOCRAWLER_DB_PATH, query, tuple(sponsor_names), "BioCrawler Catalyst Signals")

def fetch_kol_landscape(disease_term):
    """Extracts top KOLs for the therapeutic area based on PI trials."""
    condition_query = "%" + disease_term + "%"
    
    query = """
    SELECT i.investigator_name, i.affiliation as institution, COUNT(DISTINCT i.nct_id) as trials
    FROM trial_investigators i
    JOIN trial_conditions c ON i.nct_id = c.nct_id
    WHERE c.condition LIKE ? AND i.role = 'PRINCIPAL_INVESTIGATOR'
    GROUP BY i.investigator_name, i.affiliation
    ORDER BY trials DESC
    LIMIT 20;
    """
    return query_internal_db(CT_DB_PATH, query, (condition_query,), "KOL Landscape")

def generate_ta_cache(disease_term):
    print(f"=== Starting TA Landscape API Batching for: {disease_term} ===")
    ensure_cache_dir()
    
    # Generate a safe filename
    safe_term = "".join(c if c.isalnum() else "_" for c in disease_term).strip("_").lower()
    cache_file = os.path.join(CACHE_DIR, f"{safe_term}_landscape_cache.json")
    
    # Container for all fetched intelligence
    intelligence_cache = {
        "disease_term": disease_term,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pubmed_literature": [],
        "clinical_trials_data": {},
        "kol_network": [],
        "biocrawler_signals": []
    }
    
    # 1. PubMed External API Fetch
    pubmed_query = f"{disease_term} AND (Review[ptyp] OR Clinical Trial[ptyp])"
    pubmed_data = fetch_pubmed_abstracts(pubmed_query, max_results=5)
    intelligence_cache["pubmed_literature"] = pubmed_data
    
    # 2. Extract structured CT intelligence
    ct_data = fetch_trial_landscape(disease_term)
    intelligence_cache["clinical_trials_data"] = ct_data
    
    # 3. Extract KOL Network
    kol_data = fetch_kol_landscape(disease_term)
    intelligence_cache["kol_network"] = kol_data
    
    # 4. Extract BioCrawler Catalyst Signals
    if ct_data and ct_data.get("sponsors"):
        intelligence_cache["biocrawler_signals"] = fetch_biocrawler_catalysts(ct_data["sponsors"])
    
    # 5. Write to Disk
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(intelligence_cache, f, indent=4)
        
    print(f"=== Successfully Cached Intelligence to {cache_file} ===")
    return cache_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meddash TA Landscape - One-Time API Data Fetcher")
    parser.add_argument("disease", type=str, help="The therapeutic area or condition (e.g., 'KRAS', 'Lung Cancer')")
    args = parser.parse_args()
    
    generate_ta_cache(args.disease)
