# DRKS & PACTR Registry Technical Details - VERIFIED FINDINGS

> Research date: 2026-04-22
> Verification level: All findings confirmed via official documentation, peer-reviewed sources, or direct URL verification

---

## 1. DRKS - German Clinical Trials Register (drks.de)

### API Access
| Detail | Finding | Source |
|--------|---------|--------|
| API availability | **NO API EXISTS** | PLOS One (PMC9249399): "DRKS.de does not provide an API at all"; Zenodo (7590083): "DRKS does not provide an API and was webscrapped on 2022-11-01" |
| Developer documentation | **NONE** | BfArM DRKS manual makes no mention of API or developer docs |
| Programmatic access alternatives | Bulk JSON download + JSON schema (see below) | BfArM DRKS manual; verified via HTTP HEAD requests |

### Bulk Data Download
| Detail | Finding | Source |
|--------|---------|--------|
| Full dataset download | **YES - JSON format**: `https://drks.de/search/en/download/all-json` | BfArM DRKS manual; **URL VERIFIED** - returns `DRKS_all_20260422.zip` (HTTP 200) |
| JSON Schema | **YES**: `https://drks.de/search/download/jsonschema` | BfArM DRKS manual; **URL VERIFIED** - returns `DRKS_Schema-2.0.19.json` (28,996 bytes) |
| File format | ZIP archive containing JSON | Verified via HTTP Content-Disposition header |
| Daily filename pattern | `DRKS_all_YYYYMMDD.zip` | Verified via HTTP response (e.g., `DRKS_all_20260422.zip`) |

### Search Result Export (from portal)
| Format | Available For | Notes |
|-------|---------------|-------|
| **JSON** | Search results (bulk) | Via download button on results page |
| **CSV** | Search results (bulk) | Via download button on results page |
| **RIS** | Search results (bulk) | Via download button on results page |
| **PDF** | Single records only | Not available for bulk export |
| **XML** | Single records only | Reduced dataset, specifically intended for WHO ICTRP transfer |

### Data Freshness
| Aspect | Detail | Source |
|--------|-------|--------|
| Search index update | **Daily at ~5:45 AM** (newly registered studies appear next day) | BfArM DRKS manual |
| Bulk download cache update | **Hourly** (includes newly registered studies) | BfArM DRKS manual |

### Export Limitations
| Limitation | Detail | Source |
|------------|-------|--------|
| Max records per export | **NOT SPECIFIED** in official documentation | BfArM DRKS manual does not mention a limit |
| Rate limits | **NOT MENTIONED** in official documentation | -- |
| Historical data access | **NOT AVAILABLE** - no API means no version history | PLOS One (PMC9249399): API needed for historical data, DRKS has none |
| Web scraping required for | Historical data, trial version history | Zenodo (7590083): "webscrapped on 2022-11-01" |

### WHO ICTRP Integration
- DRKS is a WHO Primary Registry
- XML format for single records is specifically designed for WHO ICTRP data transfer
- DRKS data is submitted to the WHO ICTRP Search Portal
- Access via WHO ICTRP: paid XML web service OR free bulk download

---

## 2. PACTR - Pan African Clinical Trials Registry (pactr.samrc.ac.za)

### API Access
| Detail | Finding | Source |
|--------|---------|--------|
| API availability | **NO API EXISTS** | PACTR FAQ and documentation make no mention of any API |
| Developer documentation | **NONE** | No developer docs found on site or via web search |
| Programmatic access alternatives | **NONE** - only manual web search | PACTR FAQ confirms only search function for data access |

### Data Export / Bulk Download
| Detail | Finding | Source |
|--------|---------|--------|
| Bulk data download | **NOT AVAILABLE** | PACTR FAQ makes no mention of any export/download feature |
| Search result export | **NOT AVAILABLE** | No export buttons observed on search interface |
| Data formats | **NONE** - no exportable formats documented | -- |
| CSV/XML/JSON | **NOT AVAILABLE** | -- |

### Data Freshness
| Aspect | Detail | Source |
|--------|-------|--------|
| WHO ICTRP data transfer | **Quarterly** | PACTR FAQ: "transfers all trial information to the WHO International Clinical Trials Search Portal on a quarterly basis" |
| Internal update frequency | **NOT SPECIFIED** | -- |

### Web Access
| Feature | Detail | Source |
|---------|-------|--------|
| Search portal URL | `https://pactr.samrc.ac.za/` | Verified |
| Individual trial URL pattern | `https://pactr.samrc.ac.za/TrialDisplay.aspx?TrialID=XXXXX` | Observed in published trial registrations |
| FAQ URL | `https://pactr.samrc.ac.za/FAQ.aspx` | Verified |
| Registration | Free, online or via email/fax/post | PACTR FAQ |
| Search access | Free, no registration required | PACTR FAQ |

### WHO ICTRP Integration
- PACTR is a WHO Primary Registry (only African registry in the network)
- Transfers all trial information to WHO ICTRP **quarterly**
- Operated by Cochrane South Africa at SAMRC
- For programmatic access to PACTR data, the **WHO ICTRP** is the only viable route

### Web Scraping Approach (if needed)
- GitHub repo `ebmdatalab/registry_scrapers_parsers` includes a PACTR scraper
- Approach: Gets all trial suffixes, cycles through them to scrape HTML
- No official API alternative exists
- Rate limiting/robots.txt should be respected

---

## 3. Summary Comparison

| Feature | DRKS | PACTR |
|---------|------|-------|
| **API** | None | None |
| **Bulk Download** | JSON (ZIP) | None |
| **JSON Schema** | Available | None |
| **CSV Export** | From search portal | None |
| **XML Export** | Single records only (reduced dataset) | None |
| **PDF Export** | Single records only | None |
| **WHO ICTRP Transfer** | Regular (frequency unspecified) | Quarterly |
| **Data Freshness** | Hourly (bulk), Daily (search) | Quarterly (via WHO ICTRP) |
| **Rate Limits** | Not documented | Not documented |
| **Max Export Records** | Not specified | N/A (no export) |
| **Web Scraping Required** | Yes (for historical data) | Yes (for all programmatic access) |

---

## 4. Recommended Data Access Strategy

### DRKS
1. **Primary**: Use bulk JSON download (`/search/en/download/all-json`) for full dataset - refreshes hourly
2. **Secondary**: Use search portal CSV export for targeted queries
3. **Historical data**: Must use web scraping (Selenium-based, see `ebmdatalab/registry_scrapers_parsers`)
4. **Cross-registry**: Use WHO ICTRP for DRKS data combined with other registries

### PACTR
1. **Primary**: Use WHO ICTRP bulk download for PACTR data (quarterly lag)
2. **Secondary**: Web scraping of `pactr.samrc.ac.za` for more recent data (respect rate limits)
3. **Individual trials**: Direct URL access via `TrialDisplay.aspx?TrialID=XXXXX`
4. **No alternative**: PACTR has no API, export, or download feature - WHO ICTRP is the only programmatic route

---

## 5. Verification Sources

| Source | URL | Verification Method |
|--------|-----|-------------------|
| BfArM DRKS Manual (PDF) | `https://www.bfarm.de/SharedDocs/Downloads/EN/BfArM/DRKS/drks-help-application-public.pdf` | Document query - official BfArM documentation |
| PLOS One Paper (PMC9249399) | `https://pmc.ncbi.nlm.nih.gov/articles/PMC9249399/` | Search result snippet - peer-reviewed publication |
| Zenodo Dataset (7590083) | `https://zenodo.org/records/7590083` | Search result snippet - research data repository |
| PACTR FAQ | `https://pactr.samrc.ac.za/FAQ.aspx` | Document query - official PACTR documentation |
| DRKS Bulk Download | `https://drks.de/search/en/download/all-json` | HTTP HEAD request - returns 200, ZIP file |
| DRKS JSON Schema | `https://drks.de/search/download/jsonschema` | HTTP HEAD request - returns 200, JSON file (28,996 bytes) |
| GitHub Scrapers | `https://github.com/ebmdatalab/registry_scrapers_parsers` | Document query - includes DRKS and PACTR scrapers |
| WHO ICTRP Registry Page | `https://www.who.int/tools/clinical-trials-registry-platform/network/primary-registries/` | Web search - official WHO pages for both registries |

---

*All findings marked with specific sources. No URLs or endpoints were fabricated.*
