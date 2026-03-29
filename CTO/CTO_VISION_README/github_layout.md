# Meddash GitHub Monorepo Layout

> **Repository**: [`Clinical-Quant/Meddash.ai`](https://github.com/Clinical-Quant/Meddash.ai) (Private)  
> **Branch strategy**: `main` (stable) · `dev` (active work)  
> **Last updated**: 2026-03-26

---

## Directory Structure

```
meddash/                          ← Git root (C:\Users\email\.gemini\antigravity)
│
├── .gitignore                    ← Master ignore (secrets, node_modules, __pycache__, logs, agent dirs)
├── .env.example                  ← Template for environment variables (no real secrets)
│
├── Meddash_organized_backend/    ← Python backend (FastAPI + PostgreSQL + scrapers)
│   ├── 01_KOL_Data_Engine/       ← PubMed crawler, ORCID resolver, disambiguator
│   ├── 02_Data_Curation/         ← MeSH mapping, NLP enrichment
│   ├── 03_Ontology_Engine/       ← Disease criteria DB, UMLS bridge
│   ├── 04_Product_KOL_Briefs/    ← KOL export scripts, SVS calculator
│   ├── 05_Product_TA_Landscape/  ← Therapeutic area reports, DOCX exporter
│   ├── 06_Scheduling_Cron/       ← Cron job orchestration
│   ├── 07_DevOps_Observability/  ← Logs, filepaths, health monitoring
│   ├── 08_Utils/                 ← Shared utilities
│   ├── 09_Scholar_Engine/        ← Google Scholar citation sync
│   ├── EXPORT CLIENT TEXT REPORTS/ ← Generated client-facing sandbox exports
│   ├── api_server.py             ← FastAPI gateway
│   └── requirements.txt          ← Python dependencies
│
├── meddash-frontend/             ← Next.js 15 frontend (React + TypeScript)
│   ├── src/app/                  ← Pages: Dashboard, Pipeline, Sandbox, Health
│   ├── public/                   ← Static assets
│   ├── package.json              ← Node dependencies
│   └── next.config.ts            ← Next.js configuration
│
├── CTO/                          ← Strategic documentation & workflow logs
│   ├── VISION_README/            ← Summary docs, this layout file, marketing briefs
│   ├── MEDDASH_BACKEND_WORKFLOW/ ← Version 2.0 plans, bug logs, decision logs
│   ├── ARCHIVED_PAST_MISSIONS/   ← Historical decision records
│   └── building_meddash_saas/    ← SaaS iteration planning
│
└── Building_MEDDASH_USER'S_MANUAL_WORKFLOW/  ← End-user documentation
```

---

## What Gets Committed (✓) vs Ignored (✗)

| Category | Committed? | Notes |
|----------|:----------:|-------|
| Python source (`.py`) | ✓ | All backend scripts |
| TypeScript/React (`.tsx`, `.ts`) | ✓ | All frontend pages and components |
| Markdown docs (`.md`) | ✓ | Plans, logs, decision records, this file |
| SQL schema files | ✓ | Database DDL definitions |
| `requirements.txt` / `package.json` | ✓ | Dependency manifests |
| `.env` files | ✗ | Real secrets — never committed |
| `node_modules/` | ✗ | Reinstalled via `npm ci` |
| `__pycache__/` | ✗ | Python bytecode cache |
| `.next/` build dir | ✗ | Rebuilt via `npm run build` |
| `*.log` files | ✗ | Runtime logs, not source |
| Agent system dirs (`brain/`, `knowledge/`, etc.) | ✗ | Antigravity internal state |

---

## How to Commit & Push

```bash
# From the repo root (C:\Users\email\.gemini\antigravity)
git add .
git commit -m "descriptive message about what changed"
git push origin main
```

## How to Restore from Backup

```bash
# 1. Clone the repo
git clone https://github.com/Clinical-Quant/Meddash.ai.git
cd meddash

# 2. Restore backend
cd Meddash_organized_backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Restore frontend
cd ../meddash-frontend
npm ci

# 4. Add your .env file (copy from .env.example, fill in real keys)
cp .env.example Meddash_organized_backend/.env

# 5. Start services
cd ../Meddash_organized_backend && python api_server.py
cd ../meddash-frontend && npm run dev
```

## Tagging Releases

```bash
# Tag a milestone
git tag v2.0-sandbox-disambiguation
git push origin v2.0-sandbox-disambiguation

# Roll back to a tag
git checkout tags/v2.0-sandbox-disambiguation
```

---

## Security Checklist

- [ ] `.env` is listed in `.gitignore` — **never** commit real API keys
- [ ] `.env.example` exists with placeholder values for onboarding
- [ ] Database credentials are environment-variable driven, not hardcoded
- [ ] GitHub repo is set to **Private** if it contains proprietary logic
