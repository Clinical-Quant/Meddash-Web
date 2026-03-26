import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import sys

# Constants
DB_PATH = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db"
CREDENTIALS_FILE = r"c:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\meddash-crm-api-9f2f8295332e.json"
SPREADSHEET_NAME = "Meddash Phase 1 CRM V1.0"
DAILY_LEAD_LIMIT = 20

def get_google_sheet_client():
    """Authenticates and returns a Google Sheets client."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: Credentials file not found at {CREDENTIALS_FILE}")
        print("Please place your Google Service Account JSON file there.")
        sys.exit(1)

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client

def pull_daily_leads():
    """Pulls 20 new high-probability leads from the BioCrawler database."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query: Get leads that haven't been exported to CRM yet.
    # Assumes biotech_leads has companies. We will pull top 20 based on latest data.
    # For now, we'll just pull 20 companies and their top KOLs (if available) or placeholders.
    
    query = """
    SELECT 
        bl.company_name,
        bl.website_url,
        '' as contact,
        '' as role,
        '' as linkedin,
        '' as email,
        '' as contacted,
        '' as replied,
        '' as meeting,
        '' as sale,
        bl.primary_indication as notes,
        date('now') as first_contact_date,
        '' as exact_email,
        '' as next_followup_date,
        '' as replies_sentiment_string,
        'Lead' as kanban_stage
    FROM biotech_leads bl
    ORDER BY bl.last_updated DESC
    LIMIT ?
    """
    
    try:
        cursor.execute(query, (DAILY_LEAD_LIMIT,))
        leads = cursor.fetchall()
        return leads
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def push_to_sheets(client, leads):
    """Pushes the leads to the Google Sheet."""
    if not leads:
        print("No leads to push.")
        return

    try:
        # Open the spreadsheet
        sheet = client.open(SPREADSHEET_NAME).sheet1
        
        # Check headers
        headers = sheet.row_values(1)
        expected_headers = [
            "company", "website", "contact", "role", "linkedin", "email", 
            "contacted", "replied", "meeting", "sale", "notes",
            "first_contact_date", "exact_email", "next_followup_date", 
            "replies_sentiment_string", "kanban_stage"
        ]
        
        if not headers or headers != expected_headers:
            print("Row 1 doesn't match expected headers. Adding headers...")
            sheet.insert_row(expected_headers, 1)

        # Fetch existing companies to avoid duplicates
        existing_companies = set()
        try:
            col_values = sheet.col_values(1) # Company name should be in column A (1-indexed)
            if len(col_values) > 1:
                # remove header
                existing_companies = {name.strip().lower() for name in col_values[1:]}
        except Exception as e:
            print(f"Warning: Could not fetch existing companies: {e}")

        # Filter new leads
        new_leads = []
        for lead in leads:
            company_name = str(lead[0]).strip().lower()
            if company_name not in existing_companies:
                new_leads.append(list(lead))

        if not new_leads:
            print("All top leads are already in the Google Sheet. Nothing new to append.")
            return

        # Append new leads
        for lead in new_leads:
            sheet.append_row(lead)
            
        print(f"Successfully pushed {len(new_leads)} new leads to Google Sheet: '{SPREADSHEET_NAME}'")

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Error: Spreadsheet '{SPREADSHEET_NAME}' not found.")
        print("Please ensure the spreadsheet exists and is shared with the client email in your credentials JSON.")
    except Exception as e:
        print(f"An error occurred communicating with Google Sheets: {e}")

def main():
    print("Fetching top 20 leads from BioCrawler Database...")
    leads = pull_daily_leads()
    
    if not leads:
        print("No leads found in database.")
        sys.exit(0)
        
    print(f"Found {len(leads)} leads. Authenticating with Google Sheets...")
    client = get_google_sheet_client()
    
    print("Pushing data to cloud CRM...")
    push_to_sheets(client, leads)

if __name__ == "__main__":
    main()
