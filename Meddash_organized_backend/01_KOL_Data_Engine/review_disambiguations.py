"""
review_disambiguations.py — LLM-Assisted KOL Merge Review CLI  v2.0
=====================================================================
Run from the meddash folder:
    python review_disambiguations.py

Upgrade: Each candidate is silently analyzed by Gemini Flash before display.
The AI recommendation and reasoning appear at the top of each screen.
You still make the final call — the LLM is your expert advisor, not the judge.

Setup (one-time):
    Set your Gemini API key as an environment variable:
        Windows: setx GEMINI_API_KEY "your-key-here"
    Or paste it directly into GEMINI_API_KEY below.

    Get a free key at: https://aistudio.google.com/

Controls:
    a  → APPROVE  (same person — merge later with kol_merger.py)
    r  → REJECT   (different people — block from future flagging)
    s  → SKIP     (unsure — leave PENDING for later)
    q  → QUIT     (save progress and exit)
    ?  → Show this help
"""

import sqlite3
import os
import sys
import time

DB_FILE   = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"
MAX_PUBS  = 5       # Papers shown per author
SEP       = "─" * 80

# ── Gemini configuration ─────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")   # or paste key here
GEMINI_MODEL   = "gemini-2.0-flash"
USE_LLM        = bool(GEMINI_API_KEY)

try:
    if USE_LLM:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _llm = genai.GenerativeModel(GEMINI_MODEL)
except Exception as _e:
    USE_LLM = False


# ── Database helpers ──────────────────────────────────────────────────────────

def get_pending(cursor):
    cursor.execute("""
        SELECT mc.id, mc.score_total,
               mc.score_coauthor, mc.score_mesh, mc.score_name, mc.score_temporal,
               mc.kol_id_a, mc.kol_id_b,
               a.first_name || ' ' || a.last_name AS name_a,
               b.first_name || ' ' || b.last_name AS name_b
        FROM kol_merge_candidates mc
        JOIN kols a ON mc.kol_id_a = a.id
        JOIN kols b ON mc.kol_id_b = b.id
        WHERE mc.status = 'PENDING'
        ORDER BY mc.score_total DESC
    """)
    return cursor.fetchall()


def get_publications(cursor, kol_id, limit=MAX_PUBS):
    cursor.execute("""
        SELECT p.title, p.journal_name, p.published_date
        FROM publications p
        JOIN kol_authorships ka ON p.id = ka.publication_id
        WHERE ka.kol_id = ?
        ORDER BY p.published_date DESC
        LIMIT ?
    """, (kol_id, limit))
    return cursor.fetchall()


def get_coauthors(cursor, kol_id, limit=6):
    cursor.execute("""
        SELECT DISTINCT k2.first_name || ' ' || k2.last_name
        FROM kol_authorships ka1
        JOIN kol_authorships ka2 ON ka1.publication_id = ka2.publication_id
        JOIN kols k2 ON ka2.kol_id = k2.id
        WHERE ka1.kol_id = ? AND ka2.kol_id != ?
        LIMIT ?
    """, (kol_id, kol_id, limit))
    return [r[0] for r in cursor.fetchall()]


# ── LLM analysis ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert scientific bibliographer specializing in
academic author identity disambiguation. Your job: given two lists of papers
and co-authors, decide if they belong to the SAME researcher or TWO DIFFERENT
people. Be especially careful with:
- Common East Asian surnames (Zhang, Wang, Li, Chen, Kim) — these require
  very strong evidence before merging.
- Hyphenated or variant transliterations of the same name.
- Researchers who changed affiliation or research focus mid-career.

Reply ONLY in this exact format (4 lines, no extra text):
VERDICT: APPROVE | REJECT | UNCERTAIN
CONFIDENCE: HIGH | MEDIUM | LOW
REASON: <one concise sentence explaining the key evidence>
CULTURAL NOTE: <if name is from a culture with common surnames, flag this>"""


def llm_analyze(name_a, name_b, pubs_a, pubs_b, coauth_a, coauth_b,
                score_total, score_coauthor, score_mesh) -> dict:
    """Call Gemini and return a parsed dict with verdict+reasoning."""
    if not USE_LLM:
        return {"verdict": "N/A", "confidence": "N/A",
                "reason": "LLM not configured.", "cultural": ""}

    def fmt_pubs(pubs):
        lines = []
        for t, j, d in pubs:
            yr = str(d)[:4] if d else "?"
            lines.append(f"  [{yr}] {(t or 'Untitled')[:80]}")
        return "\n".join(lines) if lines else "  (no papers found)"

    prompt = f"""Two researchers may be duplicates in our database.

RESEARCHER A: {name_a}
Papers:
{fmt_pubs(pubs_a)}
Co-authors: {', '.join(coauth_a) or '(none)'}

RESEARCHER B: {name_b}
Papers:
{fmt_pubs(pubs_b)}
Co-authors: {', '.join(coauth_b) or '(none)'}

Algorithm scores (0-1): overall={score_total:.2f}, \
co-author_overlap={score_coauthor:.2f}, mesh_overlap={score_mesh:.2f}

Are these the same person?"""

    try:
        resp = _llm.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 200},
            system_instruction=SYSTEM_PROMPT
        )
        text = resp.text.strip()
        result = {"verdict": "UNCERTAIN", "confidence": "LOW",
                  "reason": text, "cultural": ""}
        for line in text.splitlines():
            if line.startswith("VERDICT:"):
                result["verdict"] = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                result["confidence"] = line.split(":", 1)[1].strip()
            elif line.startswith("REASON:"):
                result["reason"] = line.split(":", 1)[1].strip()
            elif line.startswith("CULTURAL NOTE:"):
                result["cultural"] = line.split(":", 1)[1].strip()
        return result
    except Exception as e:
        return {"verdict": "ERROR", "confidence": "N/A",
                "reason": str(e)[:120], "cultural": ""}


# ── Display ───────────────────────────────────────────────────────────────────

VERDICT_COLOR = {
    "APPROVE":   "\033[92m",   # green
    "REJECT":    "\033[91m",   # red
    "UNCERTAIN": "\033[93m",   # yellow
    "ERROR":     "\033[90m",   # grey
    "N/A":       "\033[90m",
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def clr(text, color_code):
    return f"{color_code}{text}{RESET}"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_help():
    print(f"""
  {SEP}
  CONTROLS:
    a → APPROVE   (same person — will be merged by kol_merger.py)
    r → REJECT    (different people — block from future flagging)
    s → SKIP      (unsure — leave PENDING for next session)
    q → QUIT      (saves all decisions, resume any time)
    ? → Show this help
  {SEP}
""")


def render(row, index, total, pubs_a, pubs_b, coauth_a, coauth_b, ai):
    (cid, score, s_coauth, s_mesh, s_name, s_temp,
     kid_a, kid_b, name_a, name_b) = row

    clear()

    # Header
    print(f"\n  {BOLD}{'MEDDASH  —  KOL Disambiguation Review':^76}{RESET}")
    print(f"  {'Candidate ' + str(index) + ' of ' + str(total) + '   |   ID: #' + str(cid):^76}")
    print(f"\n  {SEP}")

    # Score bar
    print(f"  {BOLD}COMPOSITE SCORE: {score:.3f}{RESET}   "
          f"[CoAuth {s_coauth:.2f}  MeSH {s_mesh:.2f}  "
          f"Name {s_name:.2f}  Temporal {s_temp:.2f}]")
    print(f"  {SEP}\n")

    # ── AI Recommendation Block ────────────────────────────────────────────
    if ai:
        verdict_raw = ai.get("verdict", "N/A")
        verdict_col = VERDICT_COLOR.get(verdict_raw.split()[0], "\033[90m")
        conf        = ai.get("confidence", "")
        reason      = ai.get("reason", "")
        cultural    = ai.get("cultural", "")

        label = clr(f"  ✦ AI VERDICT: {verdict_raw}  [{conf} CONFIDENCE]", verdict_col)
        print(BOLD + label + RESET)
        print(f"  ✦ REASON: {reason}")
        if cultural:
            print(f"  ✦ CULTURAL NOTE: {clr(cultural, VERDICT_COLOR['UNCERTAIN'])}")
    else:
        print(f"  {clr('  ✦ AI analysis unavailable (no API key)', VERDICT_COLOR['N/A'])}")

    print(f"\n  {SEP}\n")

    # Side-by-side names
    print(f"  {BOLD}{name_a.upper():^36}{RESET}    {BOLD}{name_b.upper():^36}{RESET}")
    print()

    # Papers
    print("  RECENT PAPERS:")
    max_r = max(len(pubs_a), len(pubs_b))
    for i in range(max_r):
        cell_a = cell_b = ""
        if i < len(pubs_a):
            t, j, d = pubs_a[i]
            yr = str(d)[:4] if d else "????"
            cell_a = f"[{yr}] {(t or 'Untitled')[:33]}"
        if i < len(pubs_b):
            t, j, d = pubs_b[i]
            yr = str(d)[:4] if d else "????"
            cell_b = f"[{yr}] {(t or 'Untitled')[:33]}"
        print(f"  {cell_a:<38}  {cell_b:<38}")

    # Co-authors
    print(f"\n  CO-AUTHORS:")
    print(f"  A: {', '.join(coauth_a)[:74] or '—'}")
    print(f"  B: {', '.join(coauth_b)[:74] or '—'}")

    print(f"\n  {SEP}")


def resolve(cursor, conn, cid, action, ai_verdict=""):
    status = {"a": "APPROVED", "r": "REJECTED"}.get(action, "PENDING")
    note   = {
        "a": f"Human APPROVED (AI said: {ai_verdict})",
        "r": f"Human REJECTED (AI said: {ai_verdict})"
    }.get(action, "Skipped")
    cursor.execute("""
        UPDATE kol_merge_candidates
        SET status = ?, reviewed_at = CURRENT_TIMESTAMP, notes = ?
        WHERE id = ?
    """, (status, note, cid))
    conn.commit()


# ── Main review loop ──────────────────────────────────────────────────────────

def run_review():
    conn   = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    pending = get_pending(cursor)
    total   = len(pending)

    if total == 0:
        print("\n  ✅ No pending disambiguation candidates. Database is clean!\n")
        conn.close()
        return

    llm_status = (clr("✅ Gemini Flash ACTIVE — AI recommendations enabled", "\033[92m")
                  if USE_LLM else
                  clr("⚠  No GEMINI_API_KEY — running without AI recommendations", "\033[93m"))

    print_help()
    print(f"  {llm_status}")
    print(f"\n  Found {total} pending candidates.", end=" ")
    input("Press ENTER to start review...")

    approved = rejected = skipped = 0

    for index, row in enumerate(pending, start=1):
        cid     = row[0]
        kid_a   = row[6]
        kid_b   = row[7]
        name_a  = row[8]
        name_b  = row[9]
        score   = row[1]
        s_coauth= row[2]
        s_mesh  = row[3]

        pubs_a   = get_publications(cursor, kid_a)
        pubs_b   = get_publications(cursor, kid_b)
        coauth_a = get_coauthors(cursor, kid_a)
        coauth_b = get_coauthors(cursor, kid_b)

        # Fetch AI recommendation (non-blocking spinner feel)
        ai = None
        if USE_LLM:
            print(f"\n  ⟳  Asking Gemini about candidate {index}/{total}...", end="\r")
            ai = llm_analyze(name_a, name_b, pubs_a, pubs_b,
                             coauth_a, coauth_b, score, s_coauth, s_mesh)

        render(row, index, total, pubs_a, pubs_b, coauth_a, coauth_b, ai)
        ai_verdict = ai.get("verdict", "") if ai else ""

        while True:
            raw = input("  Decision [a / r / s / q / ?]: ").strip().lower()
            if raw == "?":
                print_help()
            elif raw == "q":
                print(f"\n  Session saved. ✅ Approved: {approved}  "
                      f"❌ Rejected: {rejected}  ⏭ Skipped: {skipped}")
                print(f"  {total - index} candidates remain for next session.\n")
                conn.close()
                sys.exit(0)
            elif raw == "a":
                resolve(cursor, conn, cid, "a", ai_verdict)
                approved += 1
                break
            elif raw == "r":
                resolve(cursor, conn, cid, "r", ai_verdict)
                rejected += 1
                break
            elif raw == "s":
                skipped += 1
                break
            else:
                print("  Invalid key. Use: a / r / s / q / ?")

    print(f"\n  {SEP}")
    print(f"  ✅ All {total} candidates reviewed!")
    print(f"  Approved: {approved}   Rejected: {rejected}   Skipped: {skipped}")
    if approved:
        print(f"\n  Next step: run  python kol_merger.py  to apply the {approved} approved merges.")
    print()
    conn.close()


if __name__ == "__main__":
    run_review()
