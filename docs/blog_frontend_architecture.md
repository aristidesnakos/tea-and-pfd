# We Almost Built on Streamlit. Here's Why We Didn't.

Imagine you're a process engineer.

You type a sentence:

*"Corn stover to ethanol via dilute acid pretreatment, enzymatic hydrolysis, and co-fermentation."*

You hit submit.

And thirty seconds later — you get back a process flow diagram, a full techno-economic analysis, and an 8-sheet Excel workbook with CAPEX, OPEX, cash flow, and MESP.

That's ProcessFlow AI. NL in. Engineering artifacts out.

When it came time to build a web interface for it, the obvious choice was Streamlit. Python-native. Fast to ship. Data-science friendly. We've all used it. We've all shipped demos on it.

We chose not to.

Here's the thinking.

---

## The Short Answer

Streamlit is a demo tool. We're building a product.

The difference matters more than it sounds.

---

## What Does "Demo Tool" Actually Mean?

When you run a BioSTEAM simulation, it takes 10 to 60 seconds. That's not a bug. That's thermodynamics.

In Streamlit, that means the UI thread blocks. The spinner spins. The user waits. There is no "submit and check back later." There is no "here's your job ID, we'll email you when it's done." There is no log streaming so the user can see what's happening.

You get a frozen page and a prayer.

That's fine for a demo. You're sitting next to the person watching. You can explain what's happening.

It's not fine for a product. Users leave.

| What we need | Streamlit | Problem |
|---|---|---|
| Async job submission | No | Blocks UI thread |
| Real-time progress logs | Workarounds only | Not designed for it |
| Persistent saved runs | No | Sessions are ephemeral |
| Shareable result links | No | No URL routing |
| Custom branded UI | Very limited | Locked into Streamlit's look |
| Multi-user with auth | Third-party bolted on | Not native |
| API other tools can call | No | Can't be consumed externally |

Every one of those is a wall you'll eventually hit. And when you hit it, you're not adding a feature — you're rewriting the product.

---

## The Architecture We Chose

```
[processflow Python library]   ← already built. this is the engine.
        ↓
[FastAPI REST API]             ← wraps the library as HTTP endpoints
        ↓                            async job queue for simulations
[Next.js frontend]             ← React UI, deployable anywhere
```

Two layers. Hard separation between engine and interface.

The library doesn't know about HTTP. The API doesn't know about React. The frontend doesn't know about BioSTEAM. Each layer does one thing.

---

## Why FastAPI

The processflow library is already Python. FastAPI wraps it with near-zero friction.

A simulation job becomes:

```python
@app.post("/api/jobs")
async def submit_job(request: JobRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    background_tasks.add_task(run_simulation, job_id, request)
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    return db.get_job(job_id)
```

That's it. The simulation runs in the background. The user polls for status. The UI updates in real time. The job persists in the database whether the user's browser is open or not.

The API surface is small and obvious:

```
POST   /api/jobs              → submit a process
GET    /api/jobs/{id}         → poll status + progress
GET    /api/jobs/{id}/pfd     → download SVG
GET    /api/jobs/{id}/tea     → download XLSX
GET    /api/jobs/{id}/spec    → get ProcessSpec JSON
POST   /api/jobs/{id}/spec    → upload edited spec + re-run
GET    /api/templates         → list templates
```

And the API is a product in itself. Other tools can call it. Integrations can call it. A future mobile app can call it. Streamlit cannot be called by anything.

---

## Why Next.js

Process engineers are not all developers. The interface needs to be something a mechanical engineer at a biorefinery would open and trust.

That means real UI. Custom components. Branded design. A URL they can bookmark and share.

Streamlit looks like an internal tool. It's supposed to — it's built for internal tools.

Next.js gives us full control. The three views we need to start are not complicated:

**New Process** — text box, template picker, or JSON upload. One submit button.

**Job View** — live log of what's running. PFD renders inline. Key TEA numbers surface immediately. Download buttons for SVG and XLSX.

**History** — list of past runs. Re-run any of them. Compare two side by side.

None of that is exotic React. It's a week of focused work. And it scales — to auth, to teams, to a white-label version, to mobile — without a rewrite.

---

## The "But Streamlit Is Faster" Argument

True. A Streamlit prototype takes a day. A FastAPI + Next.js foundation takes a week.

That's the right trade for where we are.

If we needed to show investors something next Tuesday, we'd build a Streamlit demo and throw it away after. We have that option. We just don't want Streamlit to be the thing we're iterating on when real users show up.

The cost of the extra week upfront is trivially small compared to the cost of a rewrite six months from now when the walls appear.

---

## The Full Stack

```
Frontend      Next.js 14 · Tailwind CSS · shadcn/ui · React Query
Backend       FastAPI · Pydantic (already in use) · SQLAlchemy
Jobs          asyncio background tasks → Celery + Redis at scale
Database      SQLite (dev) → PostgreSQL (prod)
Storage       Local filesystem → S3
Auth          Auth.js (when ready)
Deploy        Vercel (frontend) + Railway or Render (backend)
Monitoring    Sentry
```

Nothing exotic. Everything has a clear upgrade path. SQLite becomes Postgres when you need concurrency. Background tasks become Celery when you need scale. Local storage becomes S3 when you need persistence across deploys.

The pattern is: start simple, upgrade one piece at a time, never rewrite the whole thing.

---

## The Phased Roadmap

**Phase 0 — Streamlit prototype** (optional, 1–2 days)
Internal demo only. Never shipped as the product. Useful for validating that the integration feels right before building the real thing. Then delete it.

**Phase 1 — FastAPI backend**
This is the foundation. Turns the existing processflow library into a proper service. Job queue, persistence, REST API. No frontend yet — the CLI still works and the API can be tested with curl.

**Phase 2 — Next.js frontend**
Three views. New Process, Job View, History. Deploy to Vercel + Railway. This is the product.

**Phase 3 — Full suite**
Auth, teams, process comparison, in-browser ProcessSpec editor, PDF export, more templates, CI/CD.

---

## What We Didn't Want to Build Twice

The processflow library — the NL parser, the topology engine, the BioSTEAM wrapper, the XLSX writer — took real work to get right. It's validated against the NREL 2011 corn stover benchmark. It has 39 tests. It produces a MESP within 12% of published numbers.

That work deserves a frontend that can hold it.

Not one that blocks on a 30-second simulation. Not one that loses the run when you close the tab. Not one where the URL is `localhost:8501` forever.

The architecture is the thing that determines whether the engine gets to do its job.

We chose the architecture that gets out of the way.

---

## The Takeaway

Streamlit is the right tool for a prototype you show once. FastAPI + Next.js is the right tool for a product people come back to.

The boundary between those two things is: does a user need to trust it?

If yes — the job queue, the persistence, the real-time progress, the shareable link — all of that matters. All of it requires a real backend.

We're building something engineers will use to make capital allocation decisions. A $376M total capital investment doesn't get approved on the back of a demo that freezes.

The architecture needs to match the stakes of the work it supports.

---

## Technical Notes

**Current state of the engine (v0.1.0)**
- CLI-only. No web interface exists yet.
- Validated on corn stover → ethanol (NREL 2011 design basis)
- MESP: $1.90/gal vs. $2.15/gal benchmark (12% delta)
- 39 tests passing including NREL benchmark validation
- Outputs: ProcessSpec JSON · Mermaid PFD · Graphviz SVG · 8-sheet XLSX TEA

**Simulation runtime**
BioSTEAM corn stover simulation: 15–45 seconds depending on hardware. This is the core reason synchronous Streamlit is ruled out. A job queue is not optional — it's load-bearing.

**The ProcessSpec as API contract**
The canonical intermediate representation is a Pydantic JSON model. It is already serializable, versionable, and editable. The FastAPI layer accepts it as input and returns it as output. The frontend can render it, let the user edit it, and resubmit — without touching the engine.

**Why not Gradio**
Same ceiling as Streamlit. Slightly better API auto-generation, but the async and persistence problems are identical. Built for ML demos, not engineering products.

**Why not Flask**
Flask is synchronous by default. FastAPI is async-native and uses Pydantic — which we already depend on. No reason to introduce a second web framework with less modern defaults.

**Deployment target**
Frontend → Vercel (free tier handles early traffic).
Backend → Railway or Render (Docker container, ~$7/month to start).
Total cost at launch: under $10/month.
