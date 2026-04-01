# ProcessFlow AI — Project Charter

## What This Is

ProcessFlow AI converts natural language process descriptions into Process Flow Diagrams (PFDs) and Techno-Economic Analysis (TEA) reports. It wraps BioSTEAM for simulation and uses Claude for NL parsing.

Validated against NREL 2011 corn stover ethanol benchmark: MESP ~$1.90/gal vs $2.15/gal published (within 12%).

**JSON authoring guide for new process types:** [`docs/PROCESS_SPEC_GUIDE.md`](docs/PROCESS_SPEC_GUIDE.md)

## Current State

### Completed: Open Schema + Generic TEA (v0.2.0)
- Open unit type system: any string accepted (no code changes needed per process type)
- Field name normalization: `price_per_ton`→`price_usd_per_ton`, `parameters`→`params`, etc.
- Generic TEA calculator: NPV, payback, LCOP from JSON-provided CAPEX/OPEX
- Stream components accept both `list[str]` and `dict[str, float]`
- Flexible boundary nodes (FEED, VENT, ENGINE, etc.)
- `extra="allow"` on models preserves domain-specific fields
- 81 tests passing (22 new for open schema + generic TEA)

### Completed: CLI (v0.1.0)
- Three input modes: natural language, template, ProcessSpec JSON
- Full pipeline: parse → validate → enrich → render PFD → simulate → write XLSX
- Operating manual: `docs/OPERATING_MANUAL.md`

### Completed: FastAPI REST API (Phase 1)
- All 10 API endpoints live under `src/processflow/api/`
- Background job processing via `asyncio.to_thread()` for BioSTEAM (10-30s)
- Async SQLAlchemy 2.0 + aiosqlite (SQLite)
- 22 API tests passing (`pytest tests/test_api.py -v`)
- Manually verified end-to-end: template → job → MESP $1.90/gal → artifact downloads

### NOT started: Next.js Frontend (Phase 2)
- Detailed plan exists: `.claude/plans/jiggly-forging-dewdrop.md`
- 8 build steps covering scaffold, API client, hooks, layout, 3 pages, components

## Architecture

```
src/processflow/
  schema/process_spec.py       # ProcessSpec Pydantic models (canonical IR)
  parser/nl_parser.py          # Claude API NL parser + template loader
  parser/templates/            # Reference ProcessSpec JSON templates
  topology/engine.py           # Validation + enrichment
  topology/registry.py         # Unit op → BioSTEAM class mappings
  renderer/mermaid_renderer.py # Mermaid PFD generation
  renderer/graphviz_renderer.py# Graphviz SVG generation
  tea/simulation.py            # BioSTEAM simulation wrapper
  tea/generic_tea.py           # Generic TEA (NPV/payback/LCOP from JSON CAPEX/OPEX)
  tea/xlsx_writer.py           # 8-sheet XLSX TEA report + generic TEA report
  cli.py                       # Click CLI entry point
  api/                         # FastAPI REST API (Phase 1)
    app.py                     # create_app() factory + run()
    config.py                  # Pydantic BaseSettings (PROCESSFLOW_ env prefix)
    schemas.py                 # Request/response Pydantic models
    storage.py                 # Artifact file helpers
    routes/jobs.py             # /api/jobs CRUD (7 endpoints)
    routes/templates.py        # /api/templates (2 endpoints)
    routes/health.py           # /api/health
    services/job_runner.py     # Background pipeline (mirrors cli.py)
    database/engine.py         # Async SQLAlchemy engine + get_db()
    database/models.py         # Job ORM model
    database/migrations.py     # create_tables()
tests/
  test_api.py                  # 22 API tests (httpx + in-memory SQLite)
  test_open_schema.py          # 22 tests for open schema + generic TEA
  test_schema.py, test_topology.py, test_renderer.py, test_parser.py, test_tea.py
docs/
  PROCESS_SPEC_GUIDE.md        # JSON authoring guide for new process types
  OPERATING_MANUAL.md          # CLI operating manual
  OPENROUTER_SETUP.md          # OpenRouter integration setup guide
  OPENROUTER_INTEGRATION_SUMMARY.md  # OpenRouter changes summary
  blog_frontend_architecture.md      # Architecture blog post draft
```

## API Endpoints

```
GET    /api/health                        → {"status": "ok", "version": "0.1.0"}
GET    /api/templates                     → {"templates": ["corn_stover_ethanol", ...]}
GET    /api/templates/{name}              → ProcessSpec JSON
POST   /api/jobs                          → Create job (input_type: nl|template|json)
GET    /api/jobs                          → List jobs (paginated: ?page=1&per_page=20)
GET    /api/jobs/{id}                     → Full job state + TEA metrics + artifact URLs
DELETE /api/jobs/{id}                     → Delete job + artifacts
GET    /api/jobs/{id}/artifacts/{filename}→ Download artifact file
GET    /api/jobs/{id}/spec                → ProcessSpec JSON
POST   /api/jobs/{id}/rerun              → New job from existing spec
```

## Job Lifecycle

`submitted → parsing → validating → rendering → simulating → completed`

Failed jobs get `status: "failed"` with `error_message` and `error_type`.
`NotImplementedError` from simulation → completes with warning, not failure.

## Key Decisions

- **Server-side API key**: ANTHROPIC_API_KEY configured on server, not per-user
- **Background jobs**: FastAPI BackgroundTasks + asyncio.to_thread for blocking calls
- **Denormalized TEA metrics**: MESP, TCI, AOC, IRR, NPV stored directly on Job table for fast listing
- **Artifact storage**: `data/artifacts/{job_id}/` directory per job, gitignored
- **Frontend choice**: Next.js + shadcn/ui over Streamlit (full control over UX, real component library, proper routing)

## Development Commands

```bash
# Setup
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[api,dev]"

# Run API server
processflow-api                    # starts on 0.0.0.0:8000

# Run tests
pytest tests/ -v                   # all tests (39 core + 22 API)
pytest tests/test_api.py -v        # API tests only

# CLI (still works independently)
processflow generate --template corn_stover_ethanol -o ./results/
```

## Phase 2: Next.js Frontend (NEXT SPRINT)

Full plan: `.claude/plans/jiggly-forging-dewdrop.md`

### Prerequisites
- Node.js 18+ installed
- API server running on :8000

### Build Order (8 steps)
1. Scaffold: `npx create-next-app@latest frontend --ts --tailwind --eslint --app --src-dir`
   Then: `npx shadcn@latest init && npm install @tanstack/react-query mermaid`
2. `next.config.js` — dev proxy `/api/:path*` → `localhost:8000`
3. `lib/types.ts` + `lib/api.ts` — TS types mirroring API schemas + fetch client
4. `lib/hooks.ts` — React Query hooks with 2s polling for in-progress jobs
5. `layout.tsx` — sidebar nav ("New Process", "History") + React Query provider
6. `new/page.tsx` — tabbed form (NL, Template dropdown, JSON paste) + submit
7. `jobs/[id]/page.tsx` — status stepper, inline Mermaid PFD, TEA metric cards, downloads
8. `jobs/page.tsx` — paginated job history with status badges

### Key Components
- `mermaid-viewer.tsx` — client component, renders mermaid_text via mermaid.render()
- `tea-summary.tsx` — metric card grid (shadcn Card)
- `job-form.tsx` — tabbed input form (shadcn Tabs)
- `job-status.tsx` — pipeline step indicator

### Acceptance Criteria
- `npm run dev` on :3000 with API on :8000
- Submit corn_stover_ethanol template → job completes → PFD renders inline → TEA metrics display
- Download SVG and XLSX artifacts
- History page lists jobs with pagination

