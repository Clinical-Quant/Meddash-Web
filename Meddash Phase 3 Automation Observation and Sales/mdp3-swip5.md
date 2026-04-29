# MDP3-SWIP5 — Meddash.ai Website Implementation Plan

Created: 2026-04-28
Execution mode: Tonight sprint (Dr. Don + Alfred Chief)

## A) Discovery + Architecture Decisions

- [x] A.1.1 Confirm domain DNS/base44 state
  - Found: meddash.ai resolves to 216.24.57.251 / 216.24.57.7.
  - Found: www.meddash.ai aliases to base44.onrender.com / gcp-us-west1-1.origin.onrender.com.
  - Found: lite.meddash.ai not configured yet.

- [x] A.1.2 Hosting preference
  - Chosen: Vercel primary (Cloudflare fallback).

- [x] A.1.3 Supabase strategy
  - Chosen: dedicated website tables (`catalysts`, `leads`) in Supabase; credentials to be injected next.

- [x] A.1.4 Brand palette
  - Chosen: dark tech-medical base + cyan #00D9FF + emerald #00FF88.

- [x] A.1.5 Hero feel
  - Chosen direction: sleek 3D biotech (DNA + neural node mesh + particles), premium enterprise tone.

- [x] A.1.6 Calendar interaction
  - Chosen: click-to-modal details + filters (FDA/SEC/TRIAL/CONFERENCE).

- [x] A.1.7 Email provider
  - Chosen: Resend (fastest + low cost).

- [x] A.2.1 3D complexity
  - Chosen: Level 2 (animated but performance-safe).

- [x] A.2.2 Calendar data source
  - Chosen: Supabase first-party table.

- [x] A.2.3 Build approach
  - Chosen: Alfred builds directly with live creative checkpoints.

- [x] A.2.4 Content management
  - Chosen: code/MDX now, CMS later.

## B) Project Initialization

### B.1 Dev Environment

- [ ] B.1.1 Create GitHub repo `meddash-website`
  - Blocker: needs Dr. Don GitHub target/account choice for push.

- [x] B.1.2 Initialize Next.js project
  - Created: `/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/meddash-website`

- [x] B.1.3 Install 3D deps
  - Installed: `three`, `@react-three/fiber`, `@react-three/drei`, `@react-three/postprocessing`, `@types/three`.

- [x] B.1.4 Install animation deps
  - Installed: `framer-motion`, `gsap`.

- [x] B.1.5 Install calendar deps
  - Installed: `@fullcalendar/react`, `daygrid`, `interaction`, `timegrid`.

- [x] B.1.6 Install Supabase client
  - Installed: `@supabase/supabase-js`.

- [x] B.1.7 Install UI utility deps
  - Installed: `@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, `class-variance-authority`, `clsx`, `tailwind-merge`.

- [x] B.1.8 Configure color tokens
  - Updated: `src/app/globals.css` with meddash color tokens.

- [x] B.1.9 Create folder structure
  - Created: `src/app/api/catalysts`, `src/components/{3d,ui,sections,calendar}`, `src/lib`, `src/hooks`, `src/types`, `public/models`.

### B.2 Supabase Configuration

- [ ] B.2.1 Create/confirm Supabase project
- [x] B.2.2 Prepare env template
  - Created: `.env.local.example`
- [ ] B.2.3 Create `catalysts` table
- [ ] B.2.4 Create `leads` table
- [ ] B.2.5 Enable RLS policies
- [x] B.2.6 Create Supabase client utility
  - Created: `src/lib/supabase.ts`

## C) Build Website (Tonight Execution Queue)

- [x] C.1 Build base layout + dark hero shell
  - Implemented page shell and section flow in `src/app/page.tsx`.
- [x] C.2 Implement 3D Scene container
  - Implemented R3F canvas scene in `src/components/3d/Scene.tsx`.
- [x] C.3 Add DNAHelix component
  - Implemented rotating helix in `src/components/3d/DNAHelix.tsx`.
- [x] C.4 Add NeuralNodes component
  - Implemented node + connection mesh in `src/components/3d/NeuralNodes.tsx`.
- [x] C.5 Add ParticleField component
  - Implemented deterministic particle field in `src/components/3d/ParticleField.tsx`.
- [x] C.6 Assemble Hero section + headline + CTA
  - Implemented hero overlay and CTAs in `src/components/sections/Hero.tsx`.
- [x] C.7 Add Catalyst Calendar section scaffold
  - Implemented calendar section with FullCalendar in `src/components/sections/CatalystCalendarSection.tsx`.
- [x] C.8 Add API route for catalyst fetch
  - Added `/api/catalysts` route with seed/mock events.
- [x] C.9 Add Lead capture form + POST API
  - Added `LeadFormSection` and `/api/leads` POST endpoint.
- [x] C.10 Add Features + Enterprise + Lite sections
  - Added `Features.tsx` and `EnterpriseShowcase.tsx`.
- [x] C.11 Add floating Lite corner tab
  - Added `LiteCornerTab.tsx` linking to `https://lite.meddash.ai`.
- [x] C.12 Add Header/Footer + mobile nav
  - Added `Header.tsx` + `Footer.tsx` (desktop nav done; mobile menu minimal, no drawer yet).
- [x] C.13 Local QA + lint/build
  - `npm run lint` and `npm run build` pass successfully.

## D) Domain/Subdomain Migration

- [ ] D.1 Add `lite.meddash.ai` CNAME to Base44 target
- [ ] D.2 Point `meddash.ai` to Vercel
- [ ] D.3 Verify SSL on both root + lite
- [ ] D.4 Verify redirects and no downtime regression

## E) Launch

- [ ] E.1 Vercel env vars configured
- [ ] E.2 Production deploy
- [ ] E.3 Cross-browser/mobile smoke test
- [ ] E.4 Lead form + calendar production verification

---

## Current Status Snapshot

Completed: A + most of B.1 + B.2.2 + B.2.6
In progress tonight: C (full frontend + API), then D + E

Absolute path:
`/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/mdp3-swip5.md`
