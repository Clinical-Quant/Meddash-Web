# Clinical Quant (CQ) Team Connection Architecture

## Identity & Distinction
The **Clinical Quant (CQ)** team operates on the same physical machine and architecture, cross-using identical databases, but functions on an entirely different business model.
- **Meddash (This Node):** Strictly a Medical Affairs platform. We deal in clinical trial analytics, KOL profiling, and CRM outreach. We **do not** handle financial markets.
- **Clinical Quant (CQ Node):** Strictly a Market Analyst platform. They focus exclusively on biotech catalysts, market values, and interpreting catalyst events.

## The CQ-CTO's Infrastructure
The CQ-CTO operates in a dedicated VS Code window on this same machine using:
1. **Open-Claw Architecture:** Utilizing heartbeat functions for continuous agentic workflows to stay ahead of fast-moving market news.
2. **Data Sources (External):** Twitter, Substack, Reddit, Medical Forums, SEC Filings, and generic browser integrations.
3. **Data Sources (Internal - Read Only):** Our Meddash BioCrawler and CT Engine databases. 
4. **Cloud Infrastructure:** They will create and manage a dedicated `clinical_quant` database schema inside our shared Supabase instance.

## Inter-Node Duties & Limitations
- CQ-CTO will read Meddash data to detect catalysts.
- CQ-CTO will write their market interpretations into the shared Supabase.
- The Meddash CTO (me) retains overarching architectural awareness and will provide CQ-CTO with the necessary read-access APIs and Supabase connection strings.
