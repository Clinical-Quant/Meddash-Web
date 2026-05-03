from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
AUTO_DIR = ROOT / "scripts" / "cq_automation"
sys.path.insert(0, str(AUTO_DIR))


def test_candidate_id_is_stable_and_sanitized():
    from cq_automation_common import make_candidate_id

    assert make_candidate_id("cq_catalysts", "0001655759-26-000001") == "cand-catalyst-0001655759-26-000001"
    assert make_candidate_id("cq_insider_trades", "abc/123") == "cand-trade-abc-123"


def test_rank_candidate_prioritizes_pdufa_and_recent_form4():
    from cq_candidate_selector import rank_candidate

    pdufa = {"event_type": "PDUFA", "event_date": "2026-06-01", "source_table": "cq_catalysts"}
    form4 = {"event_type": "Form 4 Purchase", "event_date": "2026-06-01", "source_table": "cq_insider_trades"}
    assert rank_candidate(pdufa) < rank_candidate(form4)


def test_build_tweet_is_no_hype_and_has_disclaimer():
    from cq_content_composer import build_tweet_text

    candidate = {
        "ticker": "ARVN",
        "event_type": "PDUFA",
        "company_name": "Arvinas",
        "event_date": "2026-06-05",
        "accession_number": "0001655759-26-000001",
    }
    text = build_tweet_text(candidate, {"research_summary": "SEC filing confirms PDUFA date."})
    assert "$ARVN" in text
    assert "Not investment advice" in text
    assert "guaranteed" not in text.lower()


def test_render_approval_package_contains_status_and_options():
    from cq_content_composer import render_approval_package

    candidate = {
        "candidate_id": "cand-catalyst-1",
        "ticker": "ARVN",
        "company_name": "Arvinas",
        "event_type": "PDUFA",
        "event_date": "2026-06-05",
        "filing_url": "https://sec.gov/example",
    }
    confirmation = {
        "verification_status": "confirmed",
        "research_summary": "Confirmed from SEC filing.",
        "confirmed_facts_json": {"drug_name": "vepdegestrant"},
    }
    md = render_approval_package([candidate], [confirmation], run_id="test-run", timestamp="2026-05-02 00:00 UTC")
    assert "PENDING DR. DON APPROVAL" in md
    assert "APPROVE" in md
    assert "ARVN" in md


def test_artifact_metadata_hashes_file(tmp_path):
    from cq_automation_common import build_artifact_metadata

    artifact = tmp_path / "artifact.xml"
    artifact.write_text("<xml>ok</xml>", encoding="utf-8")
    meta = build_artifact_metadata(
        artifact_path=artifact,
        artifact_type="form4_xml",
        candidate_id="cand-trade-1",
        ticker="CYTK",
        accession_number="0001",
        source_url="https://sec.gov/filing",
    )
    assert meta["file_size_bytes"] == len("<xml>ok</xml>")
    assert len(meta["sha256_hash"]) == 64
    assert meta["retention_status"] == "active"


def test_verification_decision_confirms_form4_purchase_without_llm():
    from cq_independent_verifier import verify_candidate_record

    candidate = {
        "candidate_id": "cand-trade-1",
        "source_table": "cq_insider_trades",
        "ticker": "CYTK",
        "event_type": "Form 4 Purchase",
        "accession_number": "0001",
        "details_json": {"insider_name": "Buyer", "shares_amount": 100, "price_per_share": 5.0},
    }
    result = verify_candidate_record(candidate, source_text="<ownershipDocument><transactionCode>P</transactionCode></ownershipDocument>")
    assert result["verification_status"] == "confirmed"
    assert "Form 4" in result["research_summary"]
