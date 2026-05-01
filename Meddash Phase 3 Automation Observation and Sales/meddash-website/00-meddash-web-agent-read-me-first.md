# Meddash Web Agent - READ ME FIRST

Who we are
- Meddash.ai is a biotech-focused therapeutic intelligence web platform.
- Core value:
  - KOL intelligence
  - catalyst tracking
  - clinical-trial search context
- Positioning is professional, biotech-buyer oriented, signal-first.

What this repository is for
- This repo is the production web surface for meddash.ai.
- It is not the full backend intelligence factory.
- Backend/data engines live in distributed repos and local pipelines.

Non-negotiable operating rules
1) Preserve existing web architecture.
2) Prefer additive changes over rewrites.
3) Keep deployments reproducible.
4) Log every meaningful session in web log folder.

Required reference files
1) Distributed repo/file-path map (use any time):
- C:\Users\email\Hermes Agent Win Files\Meddash-CQ File paths.md

2) Cloudflare + Wrangler deployment/access reference:
- C:\Users\email\.gemini\antigravity\Meddash Phase 3 Automation Observation and Sales\meddash-website\01-cloudflare-wrangler-access-details.md

3) Sequential web session logs:
- Folder:
  - C:\Users\email\.gemini\antigravity\Meddash Phase 3 Automation Observation and Sales\meddash-website\web log\
- Naming convention:
  - web-log#no<N>-YYYY-MM-DD_HHMM.md

Deployment reality (current)
- Cloudflare Pages project: meddash-web
- Domain: meddash.ai
- Deployment mode currently ad-hoc/manual via Wrangler.
- Do not assume git push auto-deploys.

Session startup checklist for any new agent
1) Read this file first.
2) Read Cloudflare access/deploy file (Document 1).
3) Read latest 2 web logs in /web log/.
4) Confirm repo path and branch.
5) Before changes: capture current live status (/, sitemap, robots, key routes).
6) After changes: build, deploy, verify, then write a new web log entry.

Current strategic intent
- Keep site stable.
- Expand SEO and conversion layers in phases.
- Avoid unnecessary platform changes.

Owner
- Dr. Don

Maintainer persona
- Alfred Chief
