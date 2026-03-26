import gspread
import sqlite3
import re
from oauth2client.service_account import ServiceAccountCredentials
import os
import sys

# Constants
CREDENTIALS_FILE = r"c:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\meddash-crm-api-9f2f8295332e.json"
SPREADSHEET_NAME = "Meddash Phase 1 CRM V1.0"
DB_PATH = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db"

def get_google_sheet_client():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: Credentials file not found at {CREDENTIALS_FILE}")
        sys.exit(1)

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client

def generate_company_slug(company_name):
    """Standardizes company names into unique slugs for matching."""
    if not company_name:
        return "unknown"
    slug = str(company_name).lower()
    suffixes = [r'\binc\b', r'\bllc\b', r'\bcorp\b', r'\bltd\b', r'\bco\b', r'\bcorporation\b', r'\blimited\b']
    for suffix in suffixes:
        slug = re.sub(suffix, '', slug)
    slug = re.sub(r'[^\w\s]', '', slug)
    slug = ' '.join(slug.split())
    return slug

def sync_websites_to_db():
    print(f"Connecting to Google Sheet: {SPREADSHEET_NAME}...")
    client = get_google_sheet_client()
    
    try:
        sheet = client.open(SPREADSHEET_NAME).sheet1
        records = sheet.get_all_values()
    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
        return

    print(f"Connecting to local Database: {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates_made = 0

    # Skip the header row
    for index, row in enumerate(records):
        if index == 0:
            continue
            
        # Column 0 is Company, Column 1 is Website  
        if len(row) > 1:  
            company = row[0].strip()
            website = row[1].strip()

        # If they entered a website and we have a company name
        if company and website:
            slug = generate_company_slug(company)
            
            # Check if this slug exists in the DB with a missing or different website
            cursor.execute("SELECT website_url FROM biotech_leads WHERE company_slug = ?", (slug,))
            result = cursor.fetchone()
            
            if result:
                db_website = result[0]
                if db_website != website:
                    # The Google Sheet has a new/different website. Update the DB!
                    try:
                        cursor.execute(
                            "UPDATE biotech_leads SET website_url = ?, last_updated = CURRENT_TIMESTAMP WHERE company_slug = ?",
                            (website, slug)
                        )
                        updates_made += 1
                        print(f"Updated DB for {company}: Added website {website}")
                    except sqlite3.Error as e:
                        print(f"Failed to update {company}: {e}")
            else:
                 print(f"Company {company} (slug: {slug}) found in Google Sheet but not in local database. Skipping.")

    conn.commit()
    conn.close()
    
    print("-" * 40)
    print(f"Reverse Sync Complete: {updates_made} database rows updated.")

if __name__ == "__main__":
    sync_websites_to_db()
