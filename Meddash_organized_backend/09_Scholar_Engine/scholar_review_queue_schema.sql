-- Script: provision_review_queue.sql
-- Run this in the Supabase SQL Editor or via migrate_review_queue.py

CREATE TABLE IF NOT EXISTS public.scholar_review_queue (
    id SERIAL PRIMARY KEY,
    kol_id TEXT NOT NULL,
    kol_name TEXT NOT NULL,
    candidate_scholar_id TEXT NOT NULL,
    candidate_name TEXT,
    candidate_affiliation TEXT,
    candidate_interests TEXT,
    disambiguation_tier_failed TEXT,
    confidence_score INTEGER DEFAULT 0,
    reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_queue_reviewed 
ON public.scholar_review_queue(reviewed);
