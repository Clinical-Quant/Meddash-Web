-- Migration Script to create the Google Scholar Metrics table
-- This should be run physically against the Supabase instance

CREATE TABLE IF NOT EXISTS public.kol_scholar_metrics (
    kol_id UUID PRIMARY KEY REFERENCES public.kols(kol_id) ON DELETE CASCADE,
    scholar_id TEXT NOT NULL UNIQUE,
    total_citations INTEGER DEFAULT 0,
    h_index INTEGER DEFAULT 0,
    i10_index INTEGER DEFAULT 0,
    last_updated_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_scholar_metrics_updated 
ON public.kol_scholar_metrics(last_updated_date);
