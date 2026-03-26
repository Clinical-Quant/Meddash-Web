# Adding Google Scholar Citations to KOL Database

## Objective
To dynamically enrich our KOL PostgreSQL database with Google Scholar metrics (Total Citations, h-index, i10-index, and publication-specific citations) and establish a weekly automated pipeline to keep these metrics continuously updated for the Next.js UI.

## The Challenge with Google Scholar
Unlike PubMed or ClinicalTrials.gov, **Google Scholar does not have an official REST API** and aggressively blocks scraping attempts (IP bans/CAPTCHAs) when queried in bulk natively.

## Proposed Architectural Solution

### 1. Data Source Selection
We cannot use standard `requests` or `BeautifulSoup` directly due to CAPTCHAs. We have two viable paths:
* **Option A: Managed Third-Party API (Recommended)** 
  * Use **SerpApi (Google Scholar Search API)**. It handles proxy rotation, headless browsers, and CAPTCHA solving natively. We send it a name, it returns clean JSON with the Author ID and citation charts.
* **Option B: Open Source + Proxies**
  * Use the Python `scholarly` library combined with a paid rotating proxy service (e.g., BrightData). `scholarly` is excellent for extracting the exact data shapes we need but requires manual proxy management to avoid rate limits.

### 2. Matching & ID Extraction (The Bootstrap Phase)
To get the Google Scholar ID for our existing and future KOLs:
1. **Query Construction:** The Python script will pull the KOL's `first_name`, `last_name`, and `institution` from the `meddash_kols_db`.
2. **Search Execution:** It will query the Google Scholar Author Search (e.g., "John Doe Harvard").
3. **ID Extraction:** The API will return the top matched author profile. We extract their unique Google Scholar ID (the `user=` parameter in their profile URL).
4. **Validation:** We will cross-reference the author's listed interests or recent publications with our PubMed data to ensure a positive match.

### 3. Database Schema Upgrades (`meddash_kols_db`)
We will add a dedicated table to our Supabase PostgreSQL cluster to prevent bloating the core KOL table:

**Table: `kol_scholar_metrics`**
* `kol_id` (Foreign Key pointing to `meddash_kols`)
* `scholar_id` (String, Unique)
* `total_citations` (Integer)
* `h_index` (Integer)
* `i10_index` (Integer)
* `last_updated_date` (Timestamp)

### 4. On-Demand Fetching via Next.js UI (Rate Limit Avoidance)
To guarantee we do not accidentally exceed the SerpApi monthly limits (e.g., 100 free searches/month), we will **NOT** use automated weekly cron jobs. 
Instead, citations will be pulled strictly on-demand via the Phase 2 KOL dashboard UI.
1. **New Script:** `09_Scholar_Engine/sync_scholar_citations.py` (Exposed via FastAPI `/api/system/run`).
2. **Execution Flow:** 
   * A user views a KOL on the frontend and clicks an explicit `[Fetch Real-Time Scholar Metrics]` button.
   * Next.js fires a POST payload via the FastAPI bridge containing the KOL's `scholar_id`.
   * The script hits the SerpApi endpoint *exactly once* for that specific KOL.
   * It performs an SQL `UPSERT`, replacing the old metrics and setting `last_updated_date` to `NOW()`.
3. **Rate Limitations to Enforce:** The Next.js UI will disable the "Fetch" button if the database says the KOL was successfully synced within the last 7 days. This prevents redundant API triggers by different users viewing the same KOL.

### 5. UI Integration (Phase 2)
* Upgrading our `/api/db/kols` FastAPI endpoint to `JOIN` the `kol_scholar_metrics` table.
* The Next.js Data Visualizer will render a new column: **"Lifetime Citations"** and **"h-index"**, giving the CEO and users an immediate gauge of a KOL's global influence beyond just the SJR journal weight.

---
**Next Steps for Approval:** 
Please review this approach. If approved, we will begin by provisioning the `kol_scholar_metrics` table in Supabase and writing the Python extractor. 

*Question:* Do you prefer we proceed with a third-party bridge like **SerpApi**, or attempt the open-source **scholarly + proxy** route?
