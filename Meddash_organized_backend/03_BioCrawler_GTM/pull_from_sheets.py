#!/usr/bin/env python3
"""Pull CRM contact data FROM Google Sheet back into biocrawler_leads.db.
Also syncs website/ticker updates from the sheet back to DB.
Run this after Dr. Don fills in contact details in the Google Sheet.
"""
import gspread
import sqlite3
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = "/mnt/c/Users/email/Downloads/service_account.json"
DB_PATH = "/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores/biocrawler_leads.db"
SHEET_NAME = "Biocrawler Biotech List"

# Column mapping (0-indexed)
COL_COMPANY = 0
COL_WEBSITE = 1
COL_TICKER = 2
COL_INDICATION = 3
COL_PHASES = 4
COL_NCT = 5
COL_COUNTRY = 6
COL_TIER = 7
COL_FUNDING = 8
COL_HIRING = 9
COL_DATE_ADDED = 10
COL_CONTACT_NAME = 11
COL_ROLE = 12
COL_LINKEDIN = 13
COL_EMAIL = 14
COL_CONTACTED = 15
COL_REPLIED = 16
COL_MEETING = 17
COL_SALE = 18
COL_KANBAN = 19
COL_FOLLOWUP = 20
COL_NOTES = 21

def slugify(name):
    """Convert company name to slug (matches biocrawler convention)."""
    return name.lower().strip().replace(' ', '-').replace(',', '').replace('.', '').replace('&', 'and')

def main():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sh = client.open(SHEET_NAME)
    ws = sh.sheet1

    all_vals = ws.get_all_values()
    if len(all_vals) < 2:
        print("No data rows in sheet (only headers). Nothing to sync.")
        return

    # Skip header row
    data_rows = all_vals[1:]
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    crm_updated = 0
    crm_inserted = 0
    db_updated = 0

    for row in data_rows:
        if not row or not row[COL_COMPANY]:
            continue
        
        company_name = row[COL_COMPANY].strip()
        slug = slugify(company_name)
        
        # Check if company exists in DB
        cur.execute("SELECT company_slug FROM biotech_leads WHERE company_slug = ?", (slug,))
        exists = cur.fetchone()
        
        # 1. Sync website/ticker back to biotech_leads
        if exists:
            website = row[COL_WEBSITE].strip() if len(row) > COL_WEBSITE else ''
            ticker = row[COL_TICKER].strip() if len(row) > COL_TICKER else ''
            if website or ticker:
                cur.execute("""
                    UPDATE biotech_leads 
                    SET website_url = COALESCE(NULLIF(?, ''), website_url),
                        ticker = COALESCE(NULLIF(?, ''), ticker)
                    WHERE company_slug = ?
                """, (website or None, ticker or None, slug))
                if cur.rowcount > 0:
                    db_updated += 1

        # 2. Sync CRM contact fields back to crm_contacts table
        contact_name = row[COL_CONTACT_NAME].strip() if len(row) > COL_CONTACT_NAME and row[COL_CONTACT_NAME].strip() else None
        if contact_name:
            role = row[COL_ROLE].strip() if len(row) > COL_ROLE and row[COL_ROLE].strip() else None
            linkedin = row[COL_LINKEDIN].strip() if len(row) > COL_LINKEDIN and row[COL_LINKEDIN].strip() else None
            email = row[COL_EMAIL].strip() if len(row) > COL_EMAIL and row[COL_EMAIL].strip() else None
            contacted = row[COL_CONTACTED].strip() if len(row) > COL_CONTACTED and row[COL_CONTACTED].strip() else None
            replied = row[COL_REPLIED].strip() if len(row) > COL_REPLIED and row[COL_REPLIED].strip() else None
            meeting = row[COL_MEETING].strip() if len(row) > COL_MEETING and row[COL_MEETING].strip() else None
            sale = row[COL_SALE].strip() if len(row) > COL_SALE and row[COL_SALE].strip() else None
            kanban = row[COL_KANBAN].strip() if len(row) > COL_KANBAN and row[COL_KANBAN].strip() else None
            followup = row[COL_FOLLOWUP].strip() if len(row) > COL_FOLLOWUP and row[COL_FOLLOWUP].strip() else None
            notes = row[COL_NOTES].strip() if len(row) > COL_NOTES and row[COL_NOTES].strip() else None

            cur.execute("""
                INSERT INTO crm_contacts (
                    company_slug, contact_name, role, linkedin_url, email,
                    contacted_date, replied, meeting_date, sale_date,
                    kanban_stage, next_followup_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_slug) DO UPDATE SET
                    contact_name = excluded.contact_name,
                    role = excluded.role,
                    linkedin_url = excluded.linkedin_url,
                    email = excluded.email,
                    contacted_date = excluded.contacted_date,
                    replied = excluded.replied,
                    meeting_date = excluded.meeting_date,
                    sale_date = excluded.sale_date,
                    kanban_stage = excluded.kanban_stage,
                    next_followup_date = excluded.next_followup_date,
                    notes = excluded.notes
            """, (slug, contact_name, role, linkedin, email,
                  contacted, replied, meeting, sale, kanban, followup, notes))
            
            if cur.rowcount > 0:
                crm_updated += 1

    conn.commit()
    conn.close()
    
    print(f"Sync complete:")
    print(f"  DB rows updated (website/ticker): {db_updated}")
    print(f"  CRM contacts upserted: {crm_updated}")
    print(f"  Total rows scanned: {len(data_rows)}")

if __name__ == '__main__':
    main()