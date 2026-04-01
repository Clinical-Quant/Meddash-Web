# Meddash.ai Architecture Mapping Results

## Core Features & Functions
1. **Clinical Trial Search**: Integrates ClinicalTrials.gov, WHO ICTRP, and EU CTR for patient matching.
2. **Clinical Summary Generator**: Converts DOIs/PubMed links into summaries (MOA, trial data, safety).
3. **Learn Any Keyword**: Deep-dive tool for receptors, drugs, and disease states.
4. **Citation Generator**: Supports AMA, Vancouver, and APA formats.
5. **Watchlists**: User-defined tracking for research areas, drugs, and diseases.
6. **Key Opinion Leaders (KOL) Hub**: Database for tracking medical experts with external links (Scholar, ResearchGate).
7. **CME Resource Center**: Aggregates courses from Medscape, CDC, and Pri-Med.
8. **AI Weekly Trends**: Automated digests of emerging research and market trends.
9. **Daily Email Alerts**: Scheduled alerts (7AM EST) for watchlist matches.

## Navigation & UI Structure
- **Global Sidebar**: Home, Search Intelligence, Watchlists, KOL Hub, Weekly Trends, CME, Profile Settings.
- **Main Dashboard**: Global search bar ("Search Medical Intelligence"), Recommendation Feed, Watchlist Cards.
- **Interaction Model**: "Evidence Actions" (credit-based system for AI tasks).

## Technical Architecture (Inferred)
- **Backend**: Base44 (API App ID: `692baf212be9bd9abfd92845`).
- **Data Sources**: ClinicalTrials.gov API, PubMed, WHO ICTRP, EU CTR, Google Scholar, ResearchGate.
- **Logic**: Python-based AI engines (LLMs for summarization, Recommendation engine for feeds).
- **Frontend**: Likely React/Next.js with Tailwind CSS.
