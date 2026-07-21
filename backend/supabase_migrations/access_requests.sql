-- ============================================================
-- Trace: Enterprise AI Underwriter
-- Migration: access_requests table
--
-- Run this SQL in the Supabase Dashboard → SQL Editor.
-- ============================================================

-- 1. Create the table
CREATE TABLE IF NOT EXISTS public.access_requests (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name          text        NOT NULL,
    work_email    text        NOT NULL,
    role          text        NOT NULL,
    requested_at  timestamptz NOT NULL DEFAULT now(),
    status        text        NOT NULL DEFAULT 'pending'
);

-- 2. Enable Row Level Security
ALTER TABLE public.access_requests ENABLE ROW LEVEL SECURITY;

-- 3. Allow the service-role key (backend) to INSERT rows freely.
--    The anon/authenticated keys used by the frontend cannot write directly.
CREATE POLICY "service_role_insert"
    ON public.access_requests
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- 4. Only the service-role key can SELECT or UPDATE rows.
--    (Admins use the Supabase Dashboard or a separate admin tool.)
CREATE POLICY "service_role_select"
    ON public.access_requests
    FOR SELECT
    TO service_role
    USING (true);

CREATE POLICY "service_role_update"
    ON public.access_requests
    FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);
