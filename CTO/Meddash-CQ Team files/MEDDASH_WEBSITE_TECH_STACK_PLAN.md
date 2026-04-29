# MedDash.ai Website Tech Stack & Implementation Plan

**Created:** 2026-04-28  
**Project:** MedDash.ai Marketing Website & Brand Platform  
**Status:** Planning Phase  

---

## 🎯 Project Overview

### Goals
- Modern, sleek marketing website for MedDash.ai
- Showcase enterprise medical affairs intelligence platform
- Feature biotech stock catalyst calendar
- Integrate MedDash Lite (Base44) as subdomain
- Enable lead capture and email registration
- Low hosting cost, agent-customizable platform

### Key Features
| Feature | Priority | Description |
|---------|----------|-------------|
| 3D Hero Animations | High | DNA helix, neural nodes, molecular structures |
| Biotech Catalyst Calendar | High | Interactive FDA/SEC/trial event tracking |
| Lead Capture | High | Email registration, industry expertise form |
| MedDash Lite Tab | Medium | Corner link to Base44 subdomain |
| Enterprise Showcase | High | Phase 2 product features |
| SEO Optimization | High | Organic search visibility |

---

## 🏗️ Recommended Tech Stack

### Core Stack Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEDDASH.AI TECH STACK                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FRONTEND LAYER                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Next.js 14 (App Router)                                 │   │
│  │  ├── React 18                                            │   │
│  │  ├── TypeScript                                          │   │
│  │  └── Server Components                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Styling & UI                                            │   │
│  │  ├── Tailwind CSS (utility-first)                       │   │
│  │  ├── shadcn/ui (component library)                      │   │
│  │  ├── Framer Motion (animations)                         │   │
│  │  └── GSAP (scroll-triggered effects)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  3D Graphics Layer                                       │   │
│  │  ├── Three.js (WebGL engine)                            │   │
│  │  ├── React Three Fiber (React renderer)                 │   │
│  │  ├── @react-three/drei (helpers)                        │   │
│  │  └── @react-three/postprocessing (effects)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DATA & CALENDAR LAYER                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Supabase (PostgreSQL + Realtime)                        │   │
│  │  ├── Catalyst events table                               │   │
│  │  ├── User registrations                                  │   │
│  │  └── Real-time subscriptions                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Calendar Components                                     │   │
│  │  ├── @fullcalendar/react                                 │   │
│  │  ├── @fullcalendar/daygrid                               │   │
│  │  └── Custom event styling                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HOSTING & INFRASTRUCTURE                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Vercel (Primary)                                        │   │
│  │  ├── Edge Functions (API routes)                        │   │
│  │  ├── Automatic deployments                               │   │
│  │  └── Free tier: 100GB bandwidth                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              OR                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Cloudflare Pages (Alternative)                          │   │
│  │  ├── Workers for edge compute                           │   │
│  │  ├── R2 for asset storage                               │   │
│  │  └── Free tier: Unlimited bandwidth                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Complete Package List

### Core Dependencies
```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    
    "three": "^0.165.0",
    "@react-three/fiber": "^8.16.0",
    "@react-three/drei": "^9.105.0",
    "@react-three/postprocessing": "^2.16.0",
    
    "framer-motion": "^11.2.0",
    "gsap": "^3.12.0",
    
    "@fullcalendar/react": "^6.1.0",
    "@fullcalendar/daygrid": "^6.1.0",
    "@fullcalendar/interaction": "^6.1.0",
    "@fullcalendar/timegrid": "^6.1.0",
    
    "@supabase/supabase-js": "^2.43.0",
    
    "tailwindcss": "^3.4.0",
    "@radix-ui/react-dialog": "^1.0.0",
    "@radix-ui/react-dropdown-menu": "^2.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.12.0",
    "@types/react": "^18.3.0",
    "@types/three": "^0.165.0",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
```

---

## 🎨 3D Animation Components

### Component Architecture

```
components/
├── 3d/
│   ├── DNAHelix.tsx          # Rotating DNA double helix
│   ├── NeuralNodes.tsx       # Connecting node network
│   ├── MoleculeGrid.tsx      # Interactive molecule structures
│   ├── ParticleField.tsx     # Floating medical particles
│   ├── DataStream.tsx        # Data flow visualization
│   ├── CellMembrane.tsx      # Animated cell boundary
│   └── Scene.tsx             # Main 3D scene container
├── ui/
│   ├── HeroSection.tsx       # Hero with 3D background
│   ├── FeatureCard.tsx       # Animated feature cards
│   └── CalendarWidget.tsx    # Catalyst calendar
└── sections/
    ├── Hero.tsx
    ├── Features.tsx
    ├── CatalystCalendar.tsx
    ├── EnterpriseShowcase.tsx
    └── Footer.tsx
```

### 3D Scene Examples

#### DNA Helix Component
```tsx
// components/3d/DNAHelix.tsx
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Float, MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'

export function DNAHelix() {
  const helixRef = useRef<THREE.Group>(null)
  
  useFrame((state) => {
    if (helixRef.current) {
      helixRef.current.rotation.y = state.clock.elapsedTime * 0.1
    }
  })
  
  return (
    <group ref={helixRef}>
      {/* DNA strand geometry */}
      <Float speed={2} rotationIntensity={0.5}>
        <mesh>
          <torusKnotGeometry args={[1, 0.3, 128, 16, 2, 3]} />
          <MeshDistortMaterial 
            color="#00D9FF" 
            distort={0.3} 
            speed={2}
          />
        </mesh>
      </Float>
    </group>
  )
}
```

#### Neural Nodes Network
```tsx
// components/3d/NeuralNodes.tsx
import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Line, Sphere } from '@react-three/drei'

export function NeuralNodes({ count = 50 }) {
  const points = useMemo(() => {
    const pts = []
    for (let i = 0; i < count; i++) {
      pts.push([
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10
      ])
    }
    return pts
  }, [count])
  
  return (
    <group>
      {points.map((pos, i) => (
        <Sphere key={i} position={pos} args={[0.1, 16, 16]}>
          <meshStandardMaterial color="#00FF88" emissive="#00FF88" />
        </Sphere>
      ))}
    </group>
  )
}
```

---

## 📅 Biotech Catalyst Calendar

### Data Model (Supabase)

```sql
-- catalysts table
CREATE TABLE catalysts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  company_name TEXT,
  event_type TEXT NOT NULL, -- 'FDA', 'SEC_8K', 'TRIAL', 'CONFERENCE'
  event_date DATE NOT NULL,
  event_time TIME,
  title TEXT NOT NULL,
  description TEXT,
  importance INTEGER DEFAULT 5, -- 1-10 scale
  data_source TEXT, -- 'sec', 'fda', 'clinicaltrials', 'manual'
  source_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_catalysts_date ON catalysts(event_date);
CREATE INDEX idx_catalysts_ticker ON catalysts(ticker);
CREATE INDEX idx_catalysts_type ON catalysts(event_type);
```

### Calendar Component

```tsx
// components/sections/CatalystCalendar.tsx
'use client'

import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'

const EVENT_COLORS = {
  FDA: '#FF4444',
  SEC_8K: '#44FF44',
  TRIAL: '#4444FF',
  CONFERENCE: '#FFAA00'
}

export function CatalystCalendar() {
  const [events, setEvents] = useState([])
  const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)
  
  useEffect(() => {
    fetchCatalysts()
  }, [])
  
  async function fetchCatalysts() {
    const { data, error } = await supabase
      .from('catalysts')
      .select('*')
      .gte('event_date', new Date().toISOString())
      .order('event_date', { ascending: true })
    
    if (!error && data) {
      setEvents(data.map(c => ({
        id: c.id,
        title: `${c.ticker} - ${c.title}`,
        start: c.event_date,
        backgroundColor: EVENT_COLORS[c.event_type],
        extendedProps: { ...c }
      })))
    }
  }
  
  return (
    <div className="calendar-container">
      <FullCalendar
        plugins={[dayGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        events={events}
        eventClick={handleEventClick}
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,dayGridWeek'
        }}
      />
    </div>
  )
}
```

### Catalyst Data Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│              CATALYST DATA PIPELINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   SEC 8-K   │    │ FDA PDUFA   │    │ Clinical    │          │
│  │   Monitor   │    │ Tracker     │    │ Trials.gov  │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                          │
│                   │  CQ Pipeline    │                          │
│                   │  (Python/Supabase)│                         │
│                   └────────┬────────┘                          │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                          │
│                   │  Supabase DB    │                          │
│                   │  catalysts table │                          │
│                   └────────┬────────┘                          │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                          │
│                   │  Next.js API    │                          │
│                   │  Real-time sync │                          │
│                   └────────┬────────┘                          │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                          │
│                   │  Calendar UI    │                          │
│                   │  (React)        │                          │
│                   └─────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Implementation Plan

### Phase 1: Project Setup (Week 1)

#### Day 1-2: Initialize Project
```bash
# Create Next.js project
npx create-next-app@latest meddash-website --typescript --tailwind --app --src-dir

# Navigate to project
cd meddash-website

# Install core dependencies
npm install three @react-three/fiber @react-three/drei @react-three/postprocessing
npm install framer-motion gsap
npm install @fullcalendar/react @fullcalendar/daygrid @fullcalendar/interaction
npm install @supabase/supabase-js

# Install UI dependencies
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install class-variance-authority clsx tailwind-merge
```

#### Day 3-4: Configure Supabase
```bash
# Set up Supabase project
# 1. Create project at supabase.com
# 2. Get project URL and anon key
# 3. Create catalysts table (see SQL above)
# 4. Enable real-time subscriptions
```

#### Day 5: Basic Project Structure
```bash
mkdir -p src/app/api
mkdir -p src/components/{3d,ui,sections}
mkdir -p src/lib
mkdir -p src/hooks
mkdir -p src/types
```

---

### Phase 2: 3D Hero Section (Week 2)

#### Day 6-7: Create 3D Scene Container
- Set up React Three Fiber canvas
- Add lighting and camera controls
- Create Scene.tsx wrapper component

#### Day 8-10: Build 3D Components
| Component | Time | Features |
|-----------|------|----------|
| DNAHelix.tsx | 4h | Rotating double helix, particles |
| NeuralNodes.tsx | 3h | Connecting nodes, animations |
| MoleculeGrid.tsx | 4h | Interactive molecules |
| ParticleField.tsx | 2h | Floating particles |
| DataStream.tsx | 3h | Data flow visualization |

#### Day 11-12: Hero Section Integration
- Combine 3D components into hero
- Add Framer Motion entrance animations
- Implement scroll-triggered effects with GSAP
- Mobile responsive optimization

---

### Phase 3: Calendar & Data (Week 3)

#### Day 13-14: Backend API Routes
```typescript
// src/app/api/catalysts/route.ts
import { createClient } from '@supabase/supabase-js'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)
  const { data, error } = await supabase
    .from('catalysts')
    .select('*')
    .order('event_date', { ascending: true })
  
  return NextResponse.json(data)
}
```

#### Day 15-17: Calendar Component
- Install and configure FullCalendar
- Create custom event styling
- Build event detail modal
- Add filter controls (FDA, SEC, Trials)

#### Day 18-19: Real-time Updates
- Set up Supabase real-time subscriptions
- Implement live calendar updates
- Add notification for new catalysts

---

### Phase 4: Lead Capture & Content (Week 4)

#### Day 20-21: Lead Capture Forms
- Email registration form
- Industry expertise questionnaire
- Newsletter signup
- Integration with email provider (Resend/SendGrid)

#### Day 22-23: Content Pages
- Features showcase
- Enterprise product descriptions
- Pricing page (Lite vs Enterprise)
- About/Team page

#### Day 24-25: MedDash Lite Integration
- Create corner tab component
- Configure subdomain routing
- Set up iframe or redirect to Base44

---

### Phase 5: Polish & Deploy (Week 5)

#### Day 26-27: SEO & Performance
- Add meta tags and Open Graph
- Implement dynamic sitemap
- Optimize 3D loading (lazy loading, compression)
- Add structured data (JSON-LD)

#### Day 28-29: Testing & QA
- Cross-browser testing
- Mobile responsiveness
- Performance profiling
- Accessibility audit

#### Day 30-31: Deployment
- Push to GitHub
- Deploy to Vercel
- Configure custom domain
- Set up analytics (Plausible/Vercel Analytics)

---

## 💰 Cost Breakdown

### Monthly Costs

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| **Vercel** | Pro | $20/mo | Required for custom domain |
| **Supabase** | Pro | $25/mo | Already in use for MedDash |
| **Domain (.ai)** | Renewal | ~$100/yr | One-time annual |
| **Three.js/R3F** | Open Source | $0 | Free forever |
| **Tailwind UI** | Open Source | $0 | Free components |
| **Cloudflare R2** | Free Tier | $0 | Asset storage backup |
| **Total** | | **~$45-55/mo** | Scales with traffic |

### Free Tier Alternative

| Service | Free Limits | Notes |
|---------|-------------|-------|
| **Vercel Free** | 100GB bandwidth, 6000 min build | Good for launch |
| **Supabase Free** | 500MB DB, 1GB storage | Requires Pro for production |
| **Cloudflare Pages** | Unlimited bandwidth | Alternative to Vercel |

---

## 🤖 Agent Development Workflow

### How Your Agents Can Help

```
┌─────────────────────────────────────────────────────────────────┐
│           AGENT-CODED DEVELOPMENT WORKFLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STEP 1: Generate Components                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Prompt for Codex/Ollama:                                │   │
│  │                                                          │   │
│  │  "Create a React Three Fiber component that renders    │   │
│  │   a DNA double helix with floating particles. The      │   │
│  │   helix should rotate slowly and have bloom effects.   │   │
│  │   Use TypeScript and @react-three/drei helpers."      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 2: Generate API Routes                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Prompt:                                                 │   │
│  │                                                          │   │
│  │  "Create a Next.js API route that fetches catalyst     │   │
│  │   events from Supabase with filtering by date range   │   │
│  │   and event type. Include error handling."             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 3: Generate Styling                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Prompt:                                                 │   │
│  │                                                          │   │
│  │  "Create Tailwind CSS classes for a modern dark-theme   │   │
│  │   hero section with gradient overlays and glassmorphism │   │
│  │  cards. Use cyan and emerald accent colors."            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 4: Generate Tests                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Prompt:                                                 │   │
│  │                                                          │   │
│  │  "Write Jest tests for the CatalystCalendar component  │   │
│  │  that verify event filtering and real-time updates."   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Prompts Library

| Task | Suggested Prompt |
|------|------------------|
| Create 3D Component | "Create a React Three Fiber [DNA helix/neural network/molecule] component with [rotation/animation/effects]. Use TypeScript and include proper lighting." |
| Create API Route | "Create a Next.js API route for [endpoint]. Connect to Supabase with error handling and TypeScript types." |
| Create UI Component | "Create a Tailwind CSS [card/button/modal] component with [glassmorphism/gradient/animation]. Use shadcn/ui patterns." |
| Generate Styles | "Create Tailwind config with [dark theme/custom colors/animations]. Include responsive breakpoints." |
| Create Tests | "Write [Jest/Cypress] tests for [component] that verify [functionality]. Include edge cases." |

---

## 📊 Performance Targets

| Metric | Target | How to Achieve |
|--------|--------|----------------|
| First Contentful Paint | < 1.5s | Server components, static generation |
| Time to Interactive | < 3s | Lazy load 3D, code splitting |
| Lighthouse Score | > 90 | Optimize images, minify CSS/JS |
| Mobile Performance | > 70 | Responsive 3D, reduce geometry |
| SEO Score | 100 | Meta tags, sitemap, structured data |

---

## 🔄 Maintenance & Updates

### Automated Catalyst Updates
```python
# Existing CQ pipeline updates catalysts automatically
# Ensure Supabase real-time is enabled
# Calendar will auto-refresh
```

### Content Updates
- Use Notion as headless CMS (optional)
- Agent Zero can update content via API
- Markdown/MDX for blog posts

### Analytics Integration
```typescript
// Add Plausible or Vercel Analytics
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>{children}</body>
      <Analytics />
    </html>
  )
}
```

---

## ✅ Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/your-repo/meddash-website.git
cd meddash-website
npm install

# Environment setup
cp .env.example .env.local
# Add Supabase credentials

# Development
npm run dev

# Production build
npm run build
npm start

# Deploy to Vercel
vercel --prod
```

---

## 📝 Next Actions

1. **Initialize project** with Next.js and all dependencies
2. **Set up Supabase** tables for catalysts
3. **Create 3D hero section** with DNA helix animation
4. **Build catalyst calendar** component
5. **Integrate lead capture** forms
6. **Deploy to Vercel** for testing

---

*This document is saved at: `/a0/CTO/Meddash-CQ Team files/MEDDASH_WEBSITE_TECH_STACK_PLAN.md`*
