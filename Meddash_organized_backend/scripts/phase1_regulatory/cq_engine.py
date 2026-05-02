#!/usr/bin/env python3
"""Clinical Quant Unified Dual-Path Engine.

Path A: 8-K catalyst extraction via edgartools markdown + Nemotron/Ollama.
Path B: Form 4 insider purchase extraction via deterministic structured XML.

Designed to be called by n8n/cron. The schedule is external: hourly during NY
market hours and every 12 hours off-market/weekends.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Iterable

import requests
from dateutil import parser as date_parser

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - optional fallback
    BeautifulSoup = None

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional for tests
    pd = None

try:
    from edgar import set_identity, get_by_accession_number
except Exception:  # pragma: no cover - edgartools optional for dry unit tests
    set_identity = None
    get_by_accession_number = None

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
CURRENT_FEED_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&output=atom"
DEFAULT_OLLAMA_HOST = "http://172.23.61.64:11434"
DEFAULT_OLLAMA_MODEL = "nemotron-3-super:cloud"
DEFAULT_EDGAR_IDENTITY = "Clinical Quant contact@meddash.ai"

VALID_EVENT_TYPES = [
    "PDUFA",
    "AdCom",
    "Phase 1 Data",
    "Phase 2 Data",
    "Phase 3 Data",
    "Interim Analysis",
    "CRL",
    "FDA Approval",
    "M&A",
    "Partnering",
    "Offering",
]

RELEVANT_ITEMS = ("8.01", "7.01", "5.02")


@dataclass
class FilingMeta:
    accession_number: str
    form_type: str
    cik: str | None
    ticker: str | None = None
    company_name: str | None = None
    filing_url: str | None = None
    updated: str | None = None


class SupabaseClient:
    """Minimal Supabase REST client using service/publishable key from .env."""

    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.key = key.strip().strip('"').strip("'")
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def select(self, table: str, select: str = "*", **filters: Any) -> list[dict[str, Any]]:
        params = {"select": select}
        for k, v in filters.items():
            params[k] = f"eq.{v}"
        r = requests.get(f"{self.url}/rest/v1/{table}", headers=self.headers, params=params, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase select {table} failed {r.status_code}: {r.text[:500]}")
        return r.json()

    def insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        r = requests.post(f"{self.url}/rest/v1/{table}", headers=self.headers, data=json.dumps(row), timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase insert {table} failed {r.status_code}: {r.text[:500]}")
        return r.json() if r.text else []

    def exists(self, table: str, accession_number: str) -> bool:
        rows = self.select(table, select="accession_number", accession_number=accession_number)
        return bool(rows)


class PostgresClient:
    """Small direct-Postgres client with the same surface as SupabaseClient.

    Used when only SUPABASE_URI is present or REST/RLS hides rows from the
    publishable key. This matches the current local Meddash backend .env.
    """

    def __init__(self, uri: str):
        import psycopg2
        import psycopg2.extras
        self.psycopg2 = psycopg2
        self.extras = psycopg2.extras
        self.conn = psycopg2.connect(uri)
        self.conn.autocommit = True

    def select(self, table: str, select: str = "*", **filters: Any) -> list[dict[str, Any]]:
        cols = select if select != "*" else "*"
        clauses = []
        vals = []
        for k, v in filters.items():
            clauses.append(f"{k} = %s")
            vals.append(v)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.conn.cursor(cursor_factory=self.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT {cols} FROM public.{table}{where}", vals)
            return [dict(r) for r in cur.fetchall()]

    def insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        keys = list(row.keys())
        vals = [row[k] for k in keys]
        placeholders = ", ".join(["%s"] * len(keys))
        columns = ", ".join(keys)
        with self.conn.cursor(cursor_factory=self.extras.RealDictCursor) as cur:
            cur.execute(f"INSERT INTO public.{table} ({columns}) VALUES ({placeholders}) RETURNING *", vals)
            return [dict(r) for r in cur.fetchall()]

    def exists(self, table: str, accession_number: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM public.{table} WHERE accession_number = %s LIMIT 1", (accession_number,))
            return cur.fetchone() is not None


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def log_event(event: str, **kwargs: Any) -> None:
    payload = {"ts": utc_now(), "event": event, **kwargs}
    print(json.dumps(payload, default=str), flush=True)


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    env = dict(os.environ)
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, val = raw.split("=", 1)
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def build_supabase(env: dict[str, str]) -> Any:
    # Prefer direct Postgres when SUPABASE_SERVICE_ROLE_KEY is not available.
    # The current local .env has a publishable REST key (RLS returns no ticker rows)
    # plus a working SUPABASE_URI, so direct Postgres is the reliable production path.
    if env.get("SUPABASE_URI") and not env.get("SUPABASE_SERVICE_ROLE_KEY"):
        return PostgresClient(env["SUPABASE_URI"])
    url = env.get("SUPABASE_URL")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_KEY") or env.get("SUPABASE_ANON_KEY")
    if url and key:
        return SupabaseClient(url, key)
    if env.get("SUPABASE_URI"):
        return PostgresClient(env["SUPABASE_URI"])
    raise RuntimeError("Missing SUPABASE_URL/key or SUPABASE_URI in .env")


def normalize_cik(cik: str | int | None) -> str | None:
    if cik is None:
        return None
    digits = re.sub(r"\D", "", str(cik))
    if not digits:
        return None
    return str(int(digits))


def load_watchlist(sb: Any, limit: int = 20000) -> dict[str, dict[str, Any]]:
    """Load CIK-keyed biotech watchlist. Falls back if boolean columns differ."""
    if isinstance(sb, PostgresClient):
        with sb.conn.cursor(cursor_factory=sb.extras.RealDictCursor) as cur:
            try:
                cur.execute(
                    """
                    SELECT ticker, cik, company_name FROM public.biotech_tickers
                    WHERE cik IS NOT NULL AND is_biotech = true AND is_active_listing = true
                    LIMIT %s
                    """,
                    (limit,),
                )
            except Exception:
                sb.conn.rollback()
                cur.execute(
                    "SELECT ticker, cik, company_name FROM public.biotech_tickers WHERE cik IS NOT NULL LIMIT %s",
                    (limit,),
                )
            rows = [dict(r) for r in cur.fetchall()]
    else:
        params = {
            "select": "ticker,cik,company_name",
            "cik": "not.is.null",
            "limit": str(limit),
        }
        # Try strict filter first. If columns are absent/RLS denies, fall back.
        rows = []
        for strict in (True, False):
            try:
                q = dict(params)
                if strict:
                    q["is_biotech"] = "eq.true"
                    q["is_active_listing"] = "eq.true"
                r = requests.get(f"{sb.url}/rest/v1/biotech_tickers", headers=sb.headers, params=q, timeout=60)
                if r.status_code >= 400:
                    raise RuntimeError(r.text[:500])
                rows = r.json()
                if rows or not strict:
                    break
            except Exception:
                if strict:
                    continue
                raise
    watch: dict[str, dict[str, Any]] = {}
    for row in rows:
        cik = normalize_cik(row.get("cik"))
        if cik:
            watch[cik] = row
    return watch


def fetch_current_feed(url: str = CURRENT_FEED_URL) -> str:
    headers = {"User-Agent": os.environ.get("EDGAR_IDENTITY", DEFAULT_EDGAR_IDENTITY)}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text


def parse_current_feed(xml_text: str) -> list[FilingMeta]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    filings: list[FilingMeta] = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        updated = (entry.findtext("a:updated", default="", namespaces=ns) or "").strip()
        link_el = entry.find("a:link", ns)
        href = link_el.attrib.get("href") if link_el is not None else None
        cat_el = entry.find("a:category", ns)
        form = cat_el.attrib.get("term") if cat_el is not None else None
        if not form:
            form = title.split(" - ", 1)[0].strip() if " - " in title else title.split()[0]
        cik_match = re.search(r"\((\d{7,10})\)", title) or re.search(r"CIK[=: ]+(\d{7,10})", summary, re.I)
        cik = normalize_cik(cik_match.group(1) if cik_match else None)
        acc_match = re.search(r"(\d{10}-\d{2}-\d{6})", (summary + " " + (href or "")))
        accession = acc_match.group(1) if acc_match else ""
        company = None
        ticker = None
        # Common title is "8-K - COMPANY (000...) (Filer)". Split on the first
        # spaced dash so hyphenated form names do not eat the company name.
        if " - " in title:
            company_part = title.split(" - ", 1)[1]
            company = re.sub(r"\s*\(\d{7,10}\).*", "", company_part).strip()
        filings.append(FilingMeta(accession_number=accession, form_type=form.strip(), cik=cik, ticker=ticker, company_name=company, filing_url=href, updated=updated))
    return [f for f in filings if f.accession_number]


def route_form_type(form_type: str) -> str:
    form = (form_type or "").upper().strip()
    if form == "4":
        return "B"
    if form == "8-K":
        return "A"
    return "skip"


def fetch_filing_obj(accession_number: str) -> Any:
    if get_by_accession_number is None:
        raise RuntimeError("edgartools import failed; install with `pip install edgartools`")
    return get_by_accession_number(accession_number)


def fallback_html_to_text(html: str) -> str:
    if BeautifulSoup is None:
        return re.sub(r"<[^>]+>", " ", html)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text("\n")


def filing_markdown(filing: Any) -> str:
    try:
        text = filing.markdown()
        if text:
            return str(text)
    except Exception:
        pass
    try:
        html = filing.html()
        if html:
            return fallback_html_to_text(str(html))
    except Exception:
        pass
    return ""


def splice_relevant_8k_sections(markdown_text: str, max_chars: int = 4000) -> str:
    text = markdown_text or ""
    if not text.strip():
        return ""
    sections: list[str] = []
    # Match item bodies from Item X.XX to next Item Y.YY, robust to markdown punctuation.
    item_pat = re.compile(r"(?is)(item\s+([0-9]{1,2}\.[0-9]{2})\b.*?)(?=\n\s*item\s+[0-9]{1,2}\.[0-9]{2}\b|\Z)")
    for match in item_pat.finditer(text):
        item_no = match.group(2)
        if item_no in RELEVANT_ITEMS:
            sections.append(match.group(1).strip())
    # Exhibit 99.1 often begins after EX-99.1 or Exhibit 99.1.
    ex_pat = re.compile(r"(?is)((?:exhibit|ex)[\s\-]*99\.1\b.*?)(?=\n\s*(?:exhibit|ex)[\s\-]*\d|\Z)")
    for match in ex_pat.finditer(text):
        sections.append(match.group(1).strip())
    out = "\n\n".join(dict.fromkeys(s for s in sections if s))
    return out[:max_chars]


def extract_json_object(text: str) -> dict[str, Any]:
    if not text:
        raise ValueError("empty LLM response")
    # Prefer fenced JSON, then first balanced object.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S | re.I)
    if fenced:
        return json.loads(fenced.group(1))
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object found")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i+1])
    raise ValueError("unterminated JSON object")


def normalize_date(value: Any) -> str | None:
    if value in (None, "", "null"):
        return None
    try:
        dt = date_parser.parse(str(value), fuzzy=True)
        return dt.date().isoformat()
    except Exception:
        return None


def validate_catalyst_result(result: dict[str, Any]) -> dict[str, Any]:
    out = dict(result or {})
    out["is_catalyst"] = bool(out.get("is_catalyst"))
    if not out["is_catalyst"]:
        return out
    if out.get("event_type") not in VALID_EVENT_TYPES:
        out["event_type"] = "Unknown"
    out["catalyst_date"] = normalize_date(out.get("catalyst_date"))
    for k in ("drug_name", "indication", "source_sentence"):
        if out.get(k) is None:
            out[k] = None
        elif not isinstance(out.get(k), str):
            out[k] = str(out.get(k))
    return out


def post_ollama_generate(host: str, payload: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
    """Post to Ollama. If WSL cannot reach Windows localhost, fallback via powershell.exe.

    Windows Ollama can be reachable from Windows PowerShell while WSL HTTP gets
    connection refused unless Ollama is bound to 0.0.0.0. The PowerShell bridge
    keeps the CQ engine usable from WSL after Dr. Don pulls `*:cloud` models on
    Windows.
    """
    try:
        r = requests.post(f"{host}/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as http_error:
        if os.name != "posix":
            raise
        ps_cmd = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "$body=[Console]::In.ReadToEnd(); "
            "Invoke-RestMethod -Uri http://127.0.0.1:11434/api/generate "
            "-Method Post -ContentType 'application/json' -Body $body | "
            "ConvertTo-Json -Compress -Depth 20",
        ]
        try:
            proc = subprocess.run(
                ps_cmd,
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=timeout + 30,
            )
        except Exception as ps_error:
            raise RuntimeError(f"Ollama HTTP failed ({http_error}); PowerShell fallback failed ({ps_error})") from ps_error
        if proc.returncode != 0:
            raise RuntimeError(
                f"Ollama HTTP failed ({http_error}); PowerShell fallback exit {proc.returncode}: {proc.stderr[:1000]}"
            )
        try:
            return json.loads(proc.stdout)
        except Exception as parse_error:
            raise RuntimeError(f"PowerShell Ollama fallback returned non-JSON: {proc.stdout[:1000]}") from parse_error


def classify_with_ollama(text: str, env: dict[str, str]) -> dict[str, Any]:
    host = env.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")
    model = env.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    prompt = f"""You are a biotech catalyst classifier. Read the following SEC 8-K filing excerpt.
Determine if it describes a biotech catalyst event. If yes, classify it.

Catalyst types: PDUFA, AdCom, Phase 1 Data, Phase 2 Data, Phase 3 Data,
                Interim Analysis, CRL, FDA Approval, M&A, Partnering, Offering

Output JSON only. Schema:
{{
  "is_catalyst": true or false,
  "event_type": "one of the types above" or null,
  "catalyst_date": "YYYY-MM-DD" or null,
  "drug_name": "string" or null,
  "indication": "string" or null,
  "source_sentence": "the exact sentence from the filing that contains the catalyst event"
}}

Rules:
- is_catalyst = true ONLY if the filing describes a specific biotech event.
- Routine corporate filings (address changes, auditor changes, insider sales, name changes) are NOT catalysts.
- If the PDUFA date is not explicitly stated but the NDA acceptance date is, compute:
  Standard Review: acceptance_date + 10 months
  Priority Review: acceptance_date + 6 months
- The source_sentence must be a direct quote from the filing text, not a paraphrase.

SEC TEXT:
{text}
"""
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0}}
    response = post_ollama_generate(host, payload, timeout=90)
    response_text = response.get("response", "")
    return validate_catalyst_result(extract_json_object(response_text))


def _row_get(row: Any, names: Iterable[str]) -> Any:
    for n in names:
        if isinstance(row, dict) and n in row:
            return row[n]
        if hasattr(row, n):
            return getattr(row, n)
        try:
            v = row[n]
            if v is not None:
                return v
        except Exception:
            pass
    return None


def _iter_rows(transactions: Any) -> list[Any]:
    if transactions is None:
        return []
    if pd is not None and isinstance(transactions, pd.DataFrame):
        return [r for _, r in transactions.iterrows()]
    if hasattr(transactions, "to_dict"):
        try:
            return transactions.to_dict("records")
        except Exception:
            pass
    if isinstance(transactions, list):
        return transactions
    return list(transactions) if hasattr(transactions, "__iter__") else []


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except Exception:
        return None


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except Exception:
        return None


def filter_purchase_transactions(transactions: Any) -> list[dict[str, Any]]:
    purchases: list[dict[str, Any]] = []
    for row in _iter_rows(transactions):
        code = _row_get(row, ["transaction_code", "code", "transactionCode", "transaction_code_value"])
        if str(code or "").strip().upper() != "P":
            continue
        insider = _row_get(row, ["reporting_name", "reportingOwnerName", "owner", "insider_name", "name"])
        date = normalize_date(_row_get(row, ["transaction_date", "transactionDate", "date"] ))
        shares = _to_int(_row_get(row, ["shares_amount", "shares", "amount", "transactionShares"] ))
        price = _to_float(_row_get(row, ["price", "price_per_share", "transactionPricePerShare"] ))
        purchases.append({
            "insider_name": insider or "Unknown",
            "transaction_date": date,
            "shares_amount": shares,
            "price_per_share": price,
        })
    return purchases


def extract_form4_purchases(filing: Any) -> list[dict[str, Any]]:
    obj = filing.obj()
    transactions = getattr(obj, "transactions", None)
    if transactions is None:
        transactions = getattr(obj, "non_derivative_transactions", None)
    return filter_purchase_transactions(transactions)


def process_path_a(filing_meta: FilingMeta, sb: SupabaseClient | None, env: dict[str, str], dry_run: bool) -> dict[str, Any]:
    filing = fetch_filing_obj(filing_meta.accession_number)
    md = filing_markdown(filing)
    spliced = splice_relevant_8k_sections(md)
    if not spliced:
        return {"status": "skipped", "reason": "no_relevant_8k_sections"}
    result = classify_with_ollama(spliced, env)
    if not result.get("is_catalyst"):
        return {"status": "skipped", "reason": "not_catalyst", "classification": result}
    row = {
        "ticker": filing_meta.ticker,
        "company_name": filing_meta.company_name,
        "accession_number": filing_meta.accession_number,
        "filing_type": "8-K",
        "event_type": result.get("event_type"),
        "catalyst_date": result.get("catalyst_date"),
        "drug_name": result.get("drug_name"),
        "indication": result.get("indication"),
        "source_sentence": result.get("source_sentence"),
        "filing_url": filing_meta.filing_url,
    }
    if dry_run or sb is None:
        return {"status": "dry_run", "row": row}
    if sb.exists("cq_catalysts", filing_meta.accession_number):
        return {"status": "dedup"}
    sb.insert("cq_catalysts", row)
    return {"status": "inserted", "row": row}


def process_path_b(filing_meta: FilingMeta, sb: SupabaseClient | None, dry_run: bool) -> dict[str, Any]:
    filing = fetch_filing_obj(filing_meta.accession_number)
    purchases = extract_form4_purchases(filing)
    if not purchases:
        return {"status": "skipped", "reason": "no_purchase_transactions"}
    rows = []
    for tx in purchases:
        rows.append({
            "ticker": filing_meta.ticker,
            "company_name": filing_meta.company_name,
            "accession_number": filing_meta.accession_number,
            "insider_name": tx.get("insider_name"),
            "transaction_date": tx.get("transaction_date"),
            "shares_amount": tx.get("shares_amount"),
            "price_per_share": tx.get("price_per_share"),
            "filing_url": filing_meta.filing_url,
        })
    if dry_run or sb is None:
        return {"status": "dry_run", "rows": rows}
    if sb.exists("cq_insider_trades", filing_meta.accession_number):
        return {"status": "dedup"}
    for row in rows:
        sb.insert("cq_insider_trades", row)
    return {"status": "inserted", "rows": rows}


def enrich_and_filter_filings(filings: list[FilingMeta], watchlist: dict[str, dict[str, Any]]) -> list[FilingMeta]:
    out: list[FilingMeta] = []
    for f in filings:
        cik = normalize_cik(f.cik)
        if not cik or cik not in watchlist:
            continue
        row = watchlist[cik]
        f.ticker = row.get("ticker")
        f.company_name = row.get("company_name") or f.company_name
        out.append(f)
    return out


def run(args: argparse.Namespace) -> dict[str, Any]:
    env = load_env()
    os.environ.setdefault("EDGAR_IDENTITY", env.get("EDGAR_IDENTITY", DEFAULT_EDGAR_IDENTITY))
    if set_identity is not None:
        set_identity(env.get("EDGAR_IDENTITY", DEFAULT_EDGAR_IDENTITY))
    sb = None if args.no_supabase else build_supabase(env)
    watchlist = {} if args.no_supabase else load_watchlist(sb)
    xml = Path(args.feed_xml).read_text(encoding="utf-8") if args.feed_xml else fetch_current_feed()
    filings = parse_current_feed(xml)
    if args.no_supabase:
        # For offline tests, process all CIK-bearing filings.
        filtered = filings
    else:
        filtered = enrich_and_filter_filings(filings, watchlist)
    if args.max_filings:
        filtered = filtered[: args.max_filings]

    summary = {"total_scanned": len(filings), "watchlist_matched": len(filtered), "routed_a": 0, "routed_b": 0, "skipped": 0, "inserted": 0, "dedup": 0, "errors": 0, "details": []}
    for filing in filtered:
        route = route_form_type(filing.form_type)
        if args.path_a_only and route != "A":
            route = "skip"
        if args.path_b_only and route != "B":
            route = "skip"
        log_event("filing_route", accession_number=filing.accession_number, form_type=filing.form_type, route=route, ticker=filing.ticker)
        if route == "skip":
            summary["skipped"] += 1
            continue
        try:
            if not args.dry_run and sb is not None:
                table = "cq_catalysts" if route == "A" else "cq_insider_trades"
                if sb.exists(table, filing.accession_number):
                    summary["dedup"] += 1
                    continue
            if route == "A":
                summary["routed_a"] += 1
                res = process_path_a(filing, sb, env, args.dry_run)
            else:
                summary["routed_b"] += 1
                res = process_path_b(filing, sb, args.dry_run)
            status = res.get("status")
            if status == "inserted":
                summary["inserted"] += 1
            elif status == "dedup":
                summary["dedup"] += 1
            elif status == "skipped":
                summary["skipped"] += 1
            summary["details"].append({"accession_number": filing.accession_number, "route": route, **res})
            log_event("filing_result", accession_number=filing.accession_number, route=route, result=res)
            time.sleep(0.1)
        except Exception as e:
            summary["errors"] += 1
            detail = {"accession_number": filing.accession_number, "route": route, "status": "error", "error": str(e)}
            summary["details"].append(detail)
            log_event("filing_error", **detail)
    log_event("summary", **{k: v for k, v in summary.items() if k != "details"})
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Clinical Quant unified dual-path SEC engine")
    p.add_argument("--dry-run", action="store_true", help="Classify/extract but do not write to Supabase")
    p.add_argument("--path-a-only", action="store_true", help="Only process 8-K catalyst path")
    p.add_argument("--path-b-only", action="store_true", help="Only process Form 4 insider trade path")
    p.add_argument("--max-filings", type=int, default=0, help="Limit filings processed after watchlist filter")
    p.add_argument("--feed-xml", help="Use local Atom XML file instead of SEC feed (testing)")
    p.add_argument("--no-supabase", action="store_true", help="Do not load watchlist or write/check Supabase (offline testing)")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.path_a_only and args.path_b_only:
        print(json.dumps({"error": "--path-a-only and --path-b-only are mutually exclusive"}))
        return 2
    try:
        result = run(args)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("errors", 0) == 0 else 1
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
