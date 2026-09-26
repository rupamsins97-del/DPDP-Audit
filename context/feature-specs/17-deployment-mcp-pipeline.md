# Unit 17 — Deployment & MCP Build Pipeline

## Goal

Use Antigravity's connected MCP servers to autonomously assemble and
deploy the already-working system: Supabase MCP applies migrations,
Cloud Run MCP deploys the FastAPI backend, Vercel/Netlify MCP deploys
the Next.js frontend — matching the Build-Time vs. Autonomous Runtime
split in `system-architecture-tech-stack-v3.md` §4.

## Design

No new product UI. This unit's "output" is a running production
system, not a screen.

## Implementation

1. Confirm every prior unit's verification checklist has already
   passed locally/staging before touching production deploy targets.
2. **Supabase MCP**: apply every migration in `supabase/migrations/`
   in order to the production Supabase project; re-verify RLS and the
   `pg_cron` retention job are active in production, not just locally.
3. **Cloud Run MCP**: containerize `apps/api` and deploy to GCP Cloud
   Run in `asia-south1`; set every variable from `.env.example` as a
   real secret (Vertex AI project/region, Supabase service-role key,
   Scrapfly key, Pub/Sub topic) — never commit real secrets to the
   repo.
4. **Vercel/Netlify MCP**: build and deploy `apps/web`, setting
   `NEXT_PUBLIC_API_URL` to the deployed Cloud Run URL.
5. Confirm the deployed frontend's SSE connection and API calls
   correctly reach the deployed backend (a live smoke test: submit a
   real audit against a real target, watch it complete on the
   production dashboard).
6. Confirm SR-1 in production: every provisioned resource (Cloud Run
   service, Vertex AI endpoint, Supabase project) is in `asia-south1`
   or `asia-south2` — check this explicitly per resource, do not
   assume the region setting propagated correctly everywhere.

## Dependencies

- Antigravity IDE with Supabase MCP, Cloud Run MCP, and Vercel/Netlify
  MCP connected and authenticated.

## Verification Checklist

- [ ] Production Supabase project shows all four tables, RLS enabled,
      and the retention cron job active
- [ ] Production Cloud Run service responds on `/health` and its
      logs show it running in `asia-south1`
- [ ] Production frontend deploy is reachable and its API calls hit
      the correct Cloud Run URL (no localhost references left over)
- [ ] A full smoke-test audit submitted against the live system
      completes and shows a real compliance score on the live
      dashboard
- [ ] Every provisioned resource's region is individually confirmed
      as `asia-south1`/`asia-south2` (SR-1) — logged in
      `progress-tracker.md` as the closing verification for the
      project
