# BioCrawler SQL Database Schema & Architecture

This document details the SQLite schema designed to store biotech leads for the MedDash KOL Intelligence funnel, ensuring idempotent ingestion (no duplicates) and fast querying for outreach.

## The Idempotent "Slug" Logic

To prevent duplicates caused by dirty data (e.g., `Acme Oncology` vs. `Acme Oncology, Inc.`), BioCrawler will generate a normalized `company_slug` to act as the Primary Key.

**Slug Generation Logic (Python):**
```python
import re

def generate_company_slug(company_name):
    """
    Standardizes company names into unique slugs for the database.
    Example: ' Acme Oncology, Therapeutics Inc. ' -> 'acme oncology therapeutics'
    """
    # Convert to lowercase
    slug = company_name.lower()
    # Remove common legal entity suffixes
    suffixes = [r'\binc\b', r'\bllc\b', r'\bcorp\b', r'\bltd\b', r'\bco\b', r'\bcorporation\b', r'\blimited\b']
    for suffix in suffixes:
        slug = re.sub(suffix, '', slug)
    # Remove punctuation
    slug = re.sub(r'[^\w\s]', '', slug)
    # Remove extra whitespace
    slug = ' '.join(slug.split())
    return slug
```

## SQLite Database Schema (`biocrawler_leads.db`)

The following schema will construct the `biotech_leads` table. It includes the newly requested parameters: `country` and `website_url`.

```sql
CREATE TABLE IF NOT EXISTS biotech_leads (
    company_slug TEXT PRIMARY KEY,       -- Uniquely identifies the company (e.g., 'acme oncology')
    company_name TEXT NOT NULL,          -- The original display name from CT.gov ('Acme Oncology, Inc.')
    primary_indication TEXT,             -- Array-like string of conditions ('Breast Neoplasms, Oncology')
    trial_phases TEXT,                   -- Array-like string ('EARLY_PHASE1, PHASE1')
    trial_nct_id TEXT,                   -- The NCT number from clinicaltrials.gov
    country TEXT,                        -- Primary location of the sponsor (e.g., 'United States', 'Canada')
    website_url TEXT DEFAULT NULL,       -- Parsed website URL, defaults to NULL if not found
    recent_funding_signal BOOLEAN DEFAULT 0, -- 1 if found in VC Portfolios / PR News
    active_hiring_signal BOOLEAN DEFAULT 0,  -- 1 if found hiring MSLs 
    tier TEXT,                           -- Calculated priority: 'A', 'B', or 'C'
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When this lead was first discovered
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- When this lead was last modified/enriched
);

-- Indexing for fast outreach querying
CREATE INDEX IF NOT EXISTS idx_tier ON biotech_leads(tier);
CREATE INDEX IF NOT EXISTS idx_country ON biotech_leads(country);

-- Relationship Graph DB (KOL Mapping)
CREATE TABLE IF NOT EXISTS associated_kols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    degree TEXT,
    institution TEXT,
    specialty TEXT,
    country TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction Table linking Leads to KOLs
CREATE TABLE IF NOT EXISTS biotech_associated_kols (
    company_slug TEXT,
    kol_id INTEGER,
    PRIMARY KEY (company_slug, kol_id),
    FOREIGN KEY (company_slug) REFERENCES biotech_leads(company_slug) ON DELETE CASCADE,
    FOREIGN KEY (kol_id) REFERENCES associated_kols(id) ON DELETE CASCADE
);
```

## The "Upsert" Ingestion Command (Idempotency)

When BioCrawler attempts to save leads to the database, it will use an `INSERT ... ON CONFLICT DO UPDATE` statement. 

**Logic:**
1. If the `company_slug` is brand new -> **INSERT** the full record.
2. If the `company_slug` exists but new signals were found (e.g., VC funding discovered after the clinical trial was already tracked) -> **UPDATE** the signals and tier, and refresh `last_updated`.

```sql
INSERT INTO biotech_leads (
    company_slug, company_name, primary_indication, trial_phases, 
    trial_nct_id, country, website_url, recent_funding_signal, 
    active_hiring_signal, tier
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(company_slug) DO UPDATE SET 
    recent_funding_signal = excluded.recent_funding_signal,
    active_hiring_signal = excluded.active_hiring_signal,
    tier = excluded.tier,
    last_updated = CURRENT_TIMESTAMP;
```

## Data Source Feeds updating Fields:
*   **ClinicalTrials.gov (Phase 1):** Sets `company_name`, `primary_indication`, `trial_phases`, `trial_nct_id`, and `country`. Initializes `tier` to 'C'.
*   **VC Portfolios (Phase 2):** Scans the DB `company_slug`s against new venture funding announcements. Updates `website_url` (often linked in VC announcements) and sets `recent_funding_signal` = True.
*   **Job Boards (Phase 3):** Scans the DB `company_slug`s against LinkedIn/Indeed. Sets `active_hiring_signal` = True.
*   **Synthesizer (Phase 4):** Evaluates signals and updates `tier` to 'A' or 'B'.
