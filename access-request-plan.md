# Access Request Flow — Implementation Plan

## Overview

When a user clicks "Request Enterprise Access" on the login screen, an inline form
expands asking for their name, work email, and role. On submit, the frontend POSTs
to a new FastAPI endpoint `/api/v1/access-request` (no auth required — the user is
not logged in). The backend validates the payload, writes a row to a new Supabase
`access_requests` table, and returns a success response. The frontend shows a toast
confirmation and collapses the form.

This follows the exact same pattern as the existing `/api/v1/evaluate-claim` →
`evaluations` table flow. The frontend never writes to Supabase directly.

---

## Sub-Tasks

### Sub-Task 1 — Create the Supabase `access_requests` table

**Intent:** Provision the DB table that will store every access request row.

**Expected Outcomes:**
- A table `access_requests` exists in Supabase with columns:
  `id` (uuid, PK), `name` (text), `work_email` (text), `role` (text),
  `requested_at` (timestamptz, default now()), `status` (text, default 'pending')
- Row-Level Security is enabled but insert is allowed for the service-role key
  (backend key); select/update are restricted to service-role only (no anon reads)

**Todo List:**
1. Write and document the SQL `CREATE TABLE` + `ALTER TABLE ENABLE ROW LEVEL SECURITY`
   + RLS policy statements in a new file `backend/supabase_migrations/access_requests.sql`
2. Instruct the user to run the SQL in the Supabase SQL editor

**Relevant Context:**
- Existing table: `evaluations` (written by `backend/app/db.py` via service-role key)
- Backend uses `SUPABASE_KEY` = service-role key (`backend/.env.example` line 31)

**Status:** `[x] complete` — SQL written to `backend/supabase_migrations/access_requests.sql`

---

### Sub-Task 2 — Add the Pydantic model + FastAPI endpoint

**Intent:** Create `POST /api/v1/access-request` — an unauthenticated endpoint that
validates the payload and inserts a row into `access_requests`.

**Expected Outcomes:**
- New Pydantic model `AccessRequest(BaseModel)` in `backend/app/models.py` with
  fields: `name: str`, `work_email: str`, `role: str`
- New route `POST /api/v1/access-request` in `backend/app/main.py` that:
  - Does NOT require `Depends(verify_token)` (user is not authenticated)
  - Validates the three fields are non-empty
  - Inserts a row into `access_requests` via `get_supabase().table("access_requests").insert(...).execute()`
  - Returns `{"status": "submitted"}` on success
  - Returns HTTP 422 on validation failure (Pydantic handles this automatically)

**Relevant Context:**
- Existing model file: `backend/app/models.py`
- Existing insert pattern: `backend/app/main.py` lines 125–134
  (`get_supabase().table("evaluations").insert({...}).execute()`)
- Existing unauthenticated route: `GET /` health check at line 88
- `get_supabase()` is imported from `backend/app/db.py`

**Status:** `[x] complete` — `AccessRequest` model added to `backend/app/models.py`; `POST /api/v1/access-request` wired in `backend/app/main.py`

---

### Sub-Task 3 — Inline form + wired submission in the frontend

**Intent:** Replace the current toast-only button with a toggled inline form that
collects name, work email, and role, POSTs to the new endpoint, and shows a
confirmation toast.

**Expected Outcomes:**
- Clicking "Request Enterprise Access" expands an inline form below the divider
  (inside the same `card_col` column, consistent with the login card layout)
- Form fields: Full Name (text), Work Email (text), Role (selectbox: Underwriter,
  Actuary, Compliance Officer, IT Administrator, Other)
- A "Submit Request" primary button and a muted "Cancel" link/button to collapse
  the form without submitting
- On submit: POSTs `{"name": ..., "work_email": ..., "role": ...}` to
  `http://localhost:8000/api/v1/access-request`
- On success (`status == "submitted"`): collapses form, fires
  `st.toast("Access request submitted — IT admin will be in touch", icon="✅")`
- On failure: shows `st.error(...)` inline within the form
- Form visibility is toggled via `st.session_state["show_access_form"]` (bool)

**Relevant Context:**
- Current button location: `frontend/app.py` inside `show_login()`, after the
  divider markdown block (lines ~836–884)
- Backend URL used elsewhere in the frontend: grep for `localhost:8000` to find
  the existing `requests.post(...)` call pattern
- Session state pattern: grep `st.session_state` in `frontend/app.py` for existing
  toggle patterns to follow

**Status:** `[x] complete` — Inline toggle form implemented in `frontend/app.py` inside `show_login()`; POSTs to `_BACKEND_URL/api/v1/access-request`

---

## Implementation Order

Sub-tasks must be done in order: 1 → 2 → 3.

Sub-task 1 produces the DB table (manual step by user).
Sub-task 2 produces the backend endpoint (can be verified independently with curl).
Sub-task 3 wires the frontend to the working endpoint.
