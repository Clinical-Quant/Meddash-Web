import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "scripts" / "phase1_regulatory"
sys.path.insert(0, str(ENGINE_DIR))

import cq_engine


def test_extract_json_from_ollama_response_with_noise():
    text = 'thinking... {"is_catalyst": true, "event_type": "PDUFA", "catalyst_date": "2026-06-05"} done'
    parsed = cq_engine.extract_json_object(text)
    assert parsed["is_catalyst"] is True
    assert parsed["event_type"] == "PDUFA"


def test_splice_relevant_sections_keeps_8k_items_and_exhibit():
    md = """
Item 1.01 Entry into Agreement
Noise agreement text.
Item 8.01 Other Events
FDA accepted the NDA and assigned a PDUFA goal date of June 5, 2026.
Item 9.01 Financial Statements and Exhibits
(d) Exhibits.
EX-99.1
Arvinas announced Vepdegestrant for breast cancer.
"""
    spliced = cq_engine.splice_relevant_8k_sections(md)
    assert "PDUFA goal date" in spliced
    assert "Vepdegestrant" in spliced
    assert "Noise agreement text" not in spliced


def test_validate_catalyst_result_normalizes_unknown_and_date():
    result = {
        "is_catalyst": True,
        "event_type": "Conference",
        "catalyst_date": "June 5, 2026",
        "drug_name": "Vepdegestrant",
        "indication": "Breast Cancer",
        "source_sentence": "FDA assigned a PDUFA date of June 5, 2026."
    }
    out = cq_engine.validate_catalyst_result(result)
    assert out["event_type"] == "Unknown"
    assert out["catalyst_date"] == "2026-06-05"


def test_route_form_type():
    assert cq_engine.route_form_type("4") == "B"
    assert cq_engine.route_form_type("8-K") == "A"
    assert cq_engine.route_form_type("10-Q") == "skip"


def test_filter_purchase_transactions_accepts_dict_rows():
    rows = [
        {"transaction_code": "P", "reporting_name": "Dr Buyer", "transaction_date": "2026-05-01", "shares_amount": "100", "price": "5.25"},
        {"transaction_code": "S", "reporting_name": "Dr Seller", "transaction_date": "2026-05-01", "shares_amount": "50", "price": "7.00"},
    ]
    purchases = cq_engine.filter_purchase_transactions(rows)
    assert len(purchases) == 1
    assert purchases[0]["insider_name"] == "Dr Buyer"
    assert purchases[0]["shares_amount"] == 100
    assert purchases[0]["price_per_share"] == 5.25


def test_parse_current_feed_extracts_accession_cik_form_url():
    xml = '''<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>8-K - ARVINAS, INC. (0001655759) (Filer)</title>
        <link href="https://www.sec.gov/Archives/edgar/data/1655759/000165575926000001/0001655759-26-000001-index.htm" />
        <summary>Accession Number: 0001655759-26-000001 Size: 1 MB</summary>
        <updated>2026-05-01T13:30:00-04:00</updated>
        <category term="8-K" />
      </entry>
    </feed>'''
    filings = cq_engine.parse_current_feed(xml)
    assert len(filings) == 1
    assert filings[0].form_type == "8-K"
    assert filings[0].cik == "1655759"
    assert filings[0].accession_number == "0001655759-26-000001"
    assert filings[0].company_name.startswith("ARVINAS")
