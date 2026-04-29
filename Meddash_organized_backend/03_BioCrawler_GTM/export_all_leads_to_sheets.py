#!/usr/bin/env python3
"""Export ALL biotech leads from biocrawler_leads.db to Google Sheet.
Replaces push_to_sheets.py (which was limited to 20 leads).
Creates headers, pushes all 655 companies, adds CRM columns for manual entry.
"""
import gspread
import sqlite3
import json
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = "/mnt/c/Users/email/Downloads/service_account.json"
DB_PATH = "/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores/biocrawler_leads.db"
SHEET_NAME = "Biocrawler Biotech List"

def main():
    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sh = client.open(SHEET_NAME)
    ws = sh.sheet1

    # Build headers: DB columns + CRM columns
    headers = [
        "company_name", "website_url", "ticker", "primary_indication", "trial_phases",
        "trial_nct_id", "country", "tier", "recent_funding_signal", "active_hiring_signal",
        "date_added",
        # CRM columns (Dr. Don fills these manually)
        "contact_name", "role", "linkedin_url", "email",
        "contacted_date", "replied", "meeting_date", "sale_date",
        "kanban_stage", "next_followup_date", "notes"
    ]

    # Read all leads from DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT company_name, website_url, ticker, primary_indication, trial_phases,
               trial_nct_id, country, tier, recent_funding_signal, active_hiring_signal,
               date_added
        FROM biotech_leads 
        ORDER BY tier ASC, company_name ASC
    """)
    rows = cur.fetchall()
    conn.close()

    # Build data rows: DB values + empty CRM columns
    data = []
    for row in rows:
        data.append([
            row['company_name'] or '',
            row['website_url'] or '',
            row['ticker'] or '',
            row['primary_indication'] or '',
            row['trial_phases'] or '',
            row['trial_nct_id'] or '',
            row['country'] or '',
            row['tier'] or '',
            'Yes' if row['recent_funding_signal'] else 'No',
            'Yes' if row['active_hiring_signal'] else 'No',
            str(row['date_added'] or ''),
            '', '', '', '',  # contact_name, role, linkedin_url, email
            '', '', '', '',  # contacted_date, replied, meeting_date, sale_date
            '', '', ''       # kanban_stage, next_followup_date, notes
        ])

    # Clear existing content and write
    ws.clear()
    ws.update(values=[headers], range_name='A1')
    print(f"Wrote headers ({len(headers)} columns)")

    # Write data in batch (gspread handles batching)
    if data:
        # Write in chunks of 100 to avoid API limits
        for i in range(0, len(data), 100):
            chunk = data[i:i+100]
            start_row = i + 2  # +2 for header row (1-indexed)
            end_row = start_row + len(chunk) - 1
            range_str = f'A{start_row}:V{end_row}'
            ws.update(values=chunk, range_name=range_str)
            print(f"Wrote rows {start_row}-{end_row} ({len(chunk)} companies)")

    print(f"\nDone! {len(data)} companies exported to: https://docs.google.com/spreadsheets/d/{sh.id}")
    
    # Summary by tier
    tier_counts = {}
    for row in rows:
        t = row['tier'] or 'Unknown'
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print("\nBy tier:")
    for t in sorted(tier_counts.keys()):
        print(f"  Tier {t}: {tier_counts[t]} companies")

if __name__ == '__main__':
    main()