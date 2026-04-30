# MDP3-SWIP5 — Meddash.ai Website Implementation Plan

Created: 2026-04-28
Last updated: 2026-04-29
Execution mode: Tonight sprint (Dr. Don + Alfred Chief)

## A) Discovery + Architecture Decisions

- [x] A.1.1 Confirm domain DNS/base44 state
  - Found and validated initial apex/www linkage to Base44/Render stack.

- [x] A.1.2 Hosting preference
  - Updated decision: Cloudflare Pages primary (replaced Vercel path due token/scope friction in runtime).

- [x] A.1.3 Lead capture persistence strategy
  - Implemented Supabase-backed lead capture via Cloudflare Pages Function.

- [x] A.1.4 Brand palette
  - Finalized dark tech-medical base + cyan/emerald accent system in global CSS.

- [x] A.1.5 Hero feel
  - Implemented sleek 3D biotech hero shell (DNA + network + particles) with enterprise tone.

- [x] A.1.6 Calendar interaction
  - Calendar section scaffold and interaction layer in place.

- [x] A.1.7 Email provider
  - Chosen: Resend (pending API key + DNS verification to activate send flow).

- [x] A.2.1 3D complexity
  - Chosen and implemented at performance-safe level.

- [x] A.2.2 Content management
  - Code-first execution now; CMS deferred.

- [x] A.2.3 Build approach
  - Live iterative build loop with direct deploy/verify cadence completed.

## B) Project Initialization

### B.1 Dev Environment

- [x] B.1.1 Create working repo/deploy workspace
  - Active deploy workspace: `/tmp/meddash-web` (used for build + Pages deploy).

- [x] B.1.2 Initialize Next.js project
- [x] B.1.3 Install 3D deps
- [x] B.1.4 Install animation deps
- [x] B.1.5 Install calendar deps
- [x] B.1.6 Install Supabase client
- [x] B.1.7 Install UI utility deps
- [x] B.1.8 Configure color tokens
- [x] B.1.9 Create folder structure

### B.2 Platform Configuration

- [x] B.2.1 Configure Cloudflare Pages project (`meddash-web`)
- [x] B.2.2 Configure static export for Pages
  - `next.config.ts`: `output: "export"`, `images.unoptimized: true`.

- [x] B.2.3 Remove conflicting Next app API routes for export path
  - Migrated dynamic backend into Cloudflare Pages Functions (`/functions/api/...`).

- [x] B.2.4 Configure Pages secrets
  - Supabase URL/service role + Telegram bot/chat secrets configured.

- [x] B.2.5 Supabase lead table create/repair
  - `public.brief_requests` created and validated.
  - Added `subscribe_updates boolean not null default true`.

## C) Website Build + Conversion Upgrades

- [x] C.1 Base layout + dark hero shell
- [x] C.2 3D Scene container
- [x] C.3 DNAHelix component
- [x] C.4 NeuralNodes component
- [x] C.5 ParticleField component
- [x] C.6 Hero headline + CTA system
  - Upgraded to stronger biotech enterprise/technical positioning copy.
  - Added dual CTA: Request Brief + Request Sample.

- [x] C.7 Catalyst Calendar section scaffold
- [x] C.8 Feature and enterprise sections
- [x] C.9 Header/Footer
  - Added top-nav LinkedIn icon after Contact.

- [x] C.10 Lite routing in nav
  - Kept Meddash Lite as separate entry (`https://lite.meddash.ai`) in top nav.

- [x] C.11 Typography system refinement
  - Finalized Option 3 stack: Sora + Manrope + JetBrains Mono.

- [x] C.12 Contact modal implementation
  - CTA-triggered modal flow implemented.

- [x] C.13 Contact form expansion
  - Added optional phone.
  - Added request-type checkboxes:
    - Intelligent KOL Brief
    - Therapeutic Area Landscape
  - Added subscribe checkbox (default checked): Meddash therapeutic area updates.

- [x] C.14 Copy corrections
  - Updated all direct contact references to `contact@meddash.ai`.

- [x] C.15 Trust + FAQ conversion section
  - Added conversion-focused trust block with concise proof cards and FAQ.

- [x] C.16 Local QA
  - Repeated `npm run build` validations passed after each major change.

## D) Domain + Hosting Migration (Executed)

- [x] D.1 Shift production from Base44 apex to Cloudflare Pages
  - `meddash.ai` now served by Cloudflare Pages.

- [x] D.2 Attach apex custom domain
  - `meddash.ai` active and returning HTTP 200.

- [x] D.3 Attach `www` custom domain
  - `www.meddash.ai` configured under Pages custom domains.

- [x] D.4 Preserve mail records during cutover
  - Zoho/SendGrid-related DNS records intentionally preserved.

- [ ] D.5 Decide final lite route strategy (subdomain vs tab-only)
  - Current production UX uses top-nav Lite link; keep/revise after final Base44-lite decision.

## E) Backend Automation (Lead Ops)

- [x] E.1 Build `/api/brief-request` Pages Function
  - Persists leads to Supabase.
  - Sends Telegram instant alert.

- [x] E.2 End-to-end production verification
  - Live POST tests confirm `supabase_ok:true` and `telegram_ok:true`.

- [x] E.3 Extend payload for conversion workflow
  - Supports multi-request types and subscribe flag.

- [x] E.4 Telegram content enrichment
  - Alert includes request type(s), contact preferences, subscribe state, notes.

- [x] E.5 Resend integration code path prepared
  - Added optional Resend send logic in function:
    - lead acknowledgment email
    - internal notification email
  - Activation pending secrets + domain verification.

## F) Remaining Launch Items

- [ ] F.1 Activate Resend in production
  - Required: `RESEND_API_KEY`, `RESEND_FROM`, `RESEND_INTERNAL_TO`, `CONTACT_EMAIL` in Cloudflare Pages secrets.

- [ ] F.2 Verify Resend domain DNS records at registrar
  - Add SPF/DKIM records provided by Resend.

- [ ] F.3 Run full email + telegram + supabase e2e test
  - Confirm all four channels in one submit path.

- [ ] F.4 Optional analytics instrumentation pass
  - Track hero CTA, modal open, form success/fail, LinkedIn click, Lite click.

---

## Current Status Snapshot

Completed:
- Production hosting migration to Cloudflare Pages
- Hero/UX/copy conversion upgrades
- Working lead pipeline (Supabase + Telegram)
- Contact identity updated to `contact@meddash.ai`
- Resend email automation code path wired (awaiting provider credentials + DNS verification)

In progress now:
- Resend activation + final e2e email verification

Absolute path:
`/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/mdp3-swip5.md`
