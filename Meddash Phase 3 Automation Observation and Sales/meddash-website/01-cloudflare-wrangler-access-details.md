# Cloudflare + Wrangler Access Details (Meddash Web)

Purpose
- This file is the onboarding reference for any new agent/session working on Meddash web deployment.
- Read this first before deploying.

Project identity
- Website repo local path:
  - C:\Users\email\.gemini\antigravity\Meddash Phase 3 Automation Observation and Sales\meddash-website
- GitHub repo:
  - https://github.com/Clinical-Quant/Meddash-Web
- Active branch for production work:
  - main

Cloudflare Pages target
- Project name:
  - meddash-web
- Project domains:
  - meddash-web.pages.dev
  - meddash.ai
  - www.meddash.ai
- Current deployment mode:
  - Ad-hoc/manual deploy via Wrangler (Git Provider shows "No")
  - Meaning: git push alone may not deploy; use wrangler deploy flow.

Credentials source of truth
- Credentials file (do not duplicate secrets elsewhere):
  - C:\Users\email\Hermes Agent Win Files\env\env + variables.md
- Expected keys in that file:
  - Cloud Flare token
  - cloud Flare Account ID

Recommended runtime export (WSL/bash)
- Parse token/account from source file, then export:
  - CLOUDFLARE_API_TOKEN
  - CLOUDFLARE_ACCOUNT_ID

Wrangler checks
- List pages projects:
  - npx wrangler pages project list
- Expected project to appear:
  - meddash-web

Standard deploy flow (Next.js + Pages)
1) Build app:
   - npm run build
2) Build Cloudflare adapter output:
   - npx @cloudflare/next-on-pages
3) Deploy static worker bundle:
   - npx wrangler pages deploy .vercel/output/static --project-name meddash-web --branch main
4) Verify live:
   - https://meddash.ai/
   - https://meddash.ai/sitemap.xml
   - https://meddash.ai/robots.txt
   - https://meddash.ai/blog

Important architecture notes
- Keep current site architecture intact.
- Use additive SEO updates only (metadata/routes/content), no core module rewrites.

Troubleshooting
- If push succeeds but site not updated:
  - Cloudflare project is likely ad-hoc mode; run wrangler deploy manually.
- If auth fails:
  - re-check token/account values in env + variables file.
- If sitemap/blog/service routes 404 after deploy:
  - verify deployment URL first (pages.dev), then custom domain propagation.

Last validated by Alfred Chief
- 2026-04-30 12:39 (local)
- Verified successful wrangler deployment and live route availability.
