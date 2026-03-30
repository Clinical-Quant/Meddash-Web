# BioCrawler CRM Engine Workspace

## Overview
This document outlines the architecture and daily workflow for the **BioCrawler CRM Engine**. This system acts as a two-way synchronization bridge between the local Meddash backend database and the cloud-based Google Sheets CRM, enabling the marketing and product teams to seamlessly interact with automatically generated leads.

## The Google Sheet CRM
**Spreadsheet Name:** `Meddash Phase 1 CRM V1.0`
This Google Sheet acts as the centralized interface for the CMO and outreach teams. It contains comprehensive lead columns including:
`Company, Website, Contact, Role, LinkedIn, Email, Contacted, Replied, Meeting, Sale, Notes, First Contact Date, Next Followup Date, Kanban Stage`

*(Note: The spreadsheet must be shared with the Service Account Email located in the `meddash-crm-api` JSON credentials).*

---

## The Push/Pull Architecture

### 1. Pushing Leads to the Cloud (`push_to_sheets.py`)
**Path:** `Meddash_organized_backend\03_BioCrawler_GTM\push_to_sheets.py`
**Function:** 
- Automatically extracts the top **20 high-probability, newly updated leads** from the local master database (`biocrawler_leads.db`).
- Intelligently checks the Google Sheet to prevent duplicate company entries.
- Appends these new leads directly to the bottom of the Google Sheet, ready for the CMO to begin outreach.

### 2. Pulling Manual Updates to Local Database (`pull_from_sheets.py`)
**Path:** `Meddash_organized_backend\03_BioCrawler_GTM\pull_from_sheets.py`
**Function:** 
- Acts as a reverse-parser. When team members manually enter or update details (such as a missing website URL) on the Google Sheet, this script captures those changes.
- It pulls the company name, standardizes it into a slug (removing "Inc", "LLC", etc.), and queries the local database.
- It detects row changes and automatically updates the local backend `biocrawler_leads.db` to permanently save the manual CRM work.

---

## Daily Operations & Batch Files
To streamline this workflow, simple Windows Batch (`.bat`) files are provided so you do not need to manually trigger Python scripts via the terminal.

- **`run_biocrawler.bat`**: Triggers the main backend scraping and lead generation protocols.
- **`run_pull_from_sheets_daily.bat`**: Triggers the reverse-parser to sync your daily manual Google Sheets work safely back down into the local master database. 

**Workflow Summary for the CMO:**
1. Let the automated Push script populate your Google Sheet with new biotech leads.
2. Conduct daily outreach, CRM management, and fill in missing contact/website data manually on the Google Sheet.
3. Run the daily batch script (`run_pull_from_sheets_daily.bat`) to permanently sync your progress and enriched data back to the core database.
