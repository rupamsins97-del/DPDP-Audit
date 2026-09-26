# Unit 01 — Repo & Environment Scaffold

## Goal

Stand up the monorepo skeleton (`apps/web`, `apps/api`, `supabase/`)
with all tooling config in place, so every later unit has a real
place to land code — with zero application logic yet.

## Design

No visual design in this unit. Establishes the file-organization
boundaries from `architecture.md` exactly, so no later unit has to
invent a folder location.

## Implementation

1. Initialize the monorepo root with a package manager workspace
   (npm/pnpm workspaces) containing `apps/web` and referencing
   `apps/api` as a separate Python project.
2. `apps/web`: scaffold Next.js 15 (App Router, React 19, TypeScript
   strict, Tailwind CSS). Add the shadcn/ui CLI and initialize it
   with the color tokens from `ui-context.md` as CSS custom
   properties in `globals.css`.
3. `apps/api`: scaffold a Python 3.12 project (FastAPI, Pydantic v2,
   `uvicorn`) with `apps/api/agents/`, `apps/api/agents/prompts/`,
   `apps/api/tools/`, `apps/api/tools/semgrep-rules/` as empty
   packages with `__init__.py` placeholders and a one-line README in
   each describing its boundary from `architecture.md`.
4. `supabase/migrations/`: empty directory, ready for Unit 02.
5. Root `.env.example` with every variable from the v3
   `master-prompts-and-ui-ux-v3.md` env spec (GCP/Vertex AI,
   Supabase, Stagehand/Scrapfly, Pub/Sub, `NEXT_PUBLIC_API_URL`) —
   values placeholder, never real secrets.
6. Root `README.md` pointing to `CLAUDE.md` as the entry point for
   anyone (human or agentic IDE) working in the repo.
7. Basic CI-less local scripts: `npm run build` (frontend), and a
   backend lint/test command (`ruff` + `pytest` stub) — both must run
   even with zero real code yet.

## Dependencies

- `next@15`, `react@19`, `tailwindcss`, `shadcn-ui` CLI
- `fastapi`, `pydantic>=2`, `uvicorn`, `ruff`, `pytest` (Python side)
- No LangGraph, Vertex AI, Stagehand, or Semgrep packages yet — those
  arrive with the units that use them (05, 06, 07, 08).

## Verification Checklist

- [ ] `apps/web` builds with `npm run build` and serves a blank
      placeholder page
- [ ] `apps/api` starts with `uvicorn` and responds on a placeholder
      root route
- [ ] Every folder named in `architecture.md`'s System Boundaries
      section exists, matching that section exactly
- [ ] `.env.example` contains every variable referenced anywhere in
      the four v3 planning docs, with no real credentials
- [ ] `ruff`/`pytest` and `npm run build` both exit 0
