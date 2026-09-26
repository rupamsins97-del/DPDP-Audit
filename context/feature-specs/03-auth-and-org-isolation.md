# Unit 03 — Auth & Org Isolation

## Goal

Wire real Supabase authentication and `organization_id` scoping into the
gateway before any feature-facing route exists, so security is never
retrofitted onto working functionality.

## Design

No new screens. Adds a session/auth gate in front of every future
`apps/web` route beyond the public landing page.

## Implementation

1. Wire Supabase Auth client in `apps/web` (`@supabase/ssr` / `@supabase/supabase-js`)
   to handle user signup and login.
2. Verify that the user-organization bootstrap trigger (created in Unit 02)
   automatically provisions an organization in `organizations` and links
   the user in `organization_members`.
3. `apps/api`: add an auth dependency (FastAPI `Depends`) that verifies the
   incoming Supabase JWT (`Authorization: Bearer <token>`) and resolves the
   authenticated user's `organization_id`. Every route added from Unit 04 onward
   takes this dependency — no route accepts a client-supplied `organization_id`
   as ground truth.
4. `apps/web`: add minimal sign-in / sign-up forms sufficient to obtain a
   session token to attach to API calls.
5. Verify end-to-end multi-tenant isolation: ensure user queries are constrained
   by `organization_id` both at the FastAPI gateway level and at the Supabase RLS level.

## Dependencies

- Supabase Auth client libraries (`@supabase/ssr` for Next.js 15, `supabase-py` or `pyjwt` for FastAPI).
- Database tables (`organizations`, `organization_members`) provisioned in Unit 02.

## Verification Checklist

- [ ] A request to any protected route without a valid session is rejected (HTTP 401) before any database call is made
- [ ] `organization_id` used in every downstream query comes strictly from the verified session
- [ ] Two different authenticated users from two different organizations cannot access each other's audits or findings
- [ ] Automatic trigger provisions an organization record upon first user registration
