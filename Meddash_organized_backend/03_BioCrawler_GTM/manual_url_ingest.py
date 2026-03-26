import sqlite3
import re
import sys
import os
import urllib.request
from bs4 import BeautifulSoup

DB_PATH = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db"

def generate_company_slug(company_name):
    """Standardizes company names into unique slugs."""
    if not company_name:
        return "unknown"
    slug = company_name.lower()
    suffixes = [r'\binc\b', r'\bllc\b', r'\bcorp\b', r'\bltd\b', r'\bco\b', r'\bcorporation\b', r'\blimited\b']
    for suffix in suffixes:
        slug = re.sub(suffix, '', slug)
    slug = re.sub(r'[^\w\s]', '', slug)
    slug = ' '.join(slug.split())
    return slug

def extract_company_name_from_url(url):
    """Fetches the webpage and extracts the company name from the title tag."""
    print(f"Fetching URL: {url}")
    try:
        # Some sites block default urllib headers, masquerade as a standard browser
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        response = urllib.request.urlopen(req, timeout=10)
        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            # Often titles are "Company Name | Home" or "Company Name - Oncology"
            delimiters = ['|', '-', '–', '—', ':']
            for d in delimiters:
                if d in title:
                    title = title.split(d)[0].strip()
            return title
        else:
            # Fallback to domain name extraction
            domain = url.split("//")[-1].split("/")[0].replace("www.", "")
            return domain.split(".")[0].capitalize()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        # Fallback to domain name
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
        return domain.split(".")[0].capitalize()

def ingest_url(url):
    """Ingests a single URL directly into the BioCrawler database as a Tier A lead."""
    if not url.startswith("http"):
        url = "https://" + url

    company_name = extract_company_name_from_url(url)
    slug = generate_company_slug(company_name)
    
    print(f"Extracted Company: {company_name}")
    print(f"Generated Slug: {slug}")

    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    INSERT INTO biotech_leads (
        company_slug, company_name, primary_indication, trial_phases, 
        trial_nct_id, country, website_url, recent_funding_signal, 
        active_hiring_signal, tier
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(company_slug) DO UPDATE SET 
        website_url = excluded.website_url,
        recent_funding_signal = 1,
        active_hiring_signal = 1,
        tier = 'A',
        last_updated = CURRENT_TIMESTAMP;
    """
    
    # We set these to Tier A ("1" for signals) so they get picked up by the CRM script
    values = (
        slug, 
        company_name, 
        "Manual Ingestion - Oncology", # Default indication, can be updated later
        "Phase 1/2", 
        "Manual", 
        "United States", 
        url, 
        1, 
        1, 
        'A'
    )
    
    try:
        cursor.execute(query, values)
        conn.commit()
        print(f"Success! {company_name} ingested into the database as a Tier A lead.")
    except sqlite3.Error as e:
        print(f"Database error during insertion: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manual_url_ingest.py <url1> <url2> ...")
        sys.exit(1)
        
    urls = sys.argv[1:]
    for url in urls:
        ingest_url(url)
        print("-" * 40)
