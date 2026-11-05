# Inkloom AI

> **Intelligent Brand-Governance Platform**  
> Evaluates marketing and communication content against an organisation's approved brand guidelines, facts, terminology, and tone standards. Final approval remains with human reviewers.

---

## 1. Product Overview

Inkloom AI helps brand marketing teams and compliance officers govern communication before publication. Instead of vague suggestions, the platform explains:
- **What is wrong:** exact text quote identified in the submitted draft.
- **Where the problem occurs:** character offsets and sentence context.
- **Which approved guideline or fact is relevant:** stable brand knowledge identifiers (e.g. `GUIDE-001`, `FACT-002`, `TERM-001`).
- **Why the content is problematic:** evidence-backed reasoning.
- **How the content can be improved:** concrete, brand-aligned correction.
- **Human reviewer authority:** final decisions (Approve, Request Revisions, Reject) are committed by designated human reviewers.

---

## 2. Architecture

Inkloom AI employs a **hybrid architecture**:
1. **Deterministic Rule Engine:** instant, reliable validation of exact and inflected prohibited terminology, explicit guarantee claims, and unapproved outcome timeframes.
2. **Contextual AI (Google Gemini):** evaluates tone, semantic nuance, unsupported claims, and extracts positive brand observations with strict structured JSON output (`AIAnalysisOutput`).
3. **Grounding Validator:** verifies every guideline and fact ID against the database knowledge, sanitises em dashes, prevents hallucinated references, and deterministically derives compliance status.
4. **Append-Only Persistence:** versions, runs, findings, and reviews are preserved immutably.

```
┌────────────────────────────────┐         ┌────────────────────────────────┐
│   React 19 + TypeScript SPA   │  REST   │      FastAPI Backend Engine    │
│  (Tailwind CSS, Lora, Sans)   ├────────►│  (Python 3.13, Pydantic v2)    │
└────────────────────────────────┘         └───────────────┬────────────────┘
                                                           │
                                        ┌──────────────────┴──────────────────┐
                                        ▼                                     ▼
                        ┌───────────────────────────────┐     ┌───────────────────────────────┐
                        │   Deterministic Rule Engine   │     │    Google GenAI SDK (Gemini)  │
                        │ (Terms, Timeframes, Outcomes) │     │ (Tone, Semantic Claims, JSON) │
                        └───────────────┬───────────────┘     └───────────────┬───────────────┘
                                        │                                     │
                                        └──────────────────┬──────────────────┘
                                                           ▼
                                        ┌─────────────────────────────────────┐
                                        │ Grounding & Deduplication Validator │
                                        └──────────────────┬──────────────────┘
                                                           ▼
                                        ┌─────────────────────────────────────┐
                                        │      Supabase PostgreSQL DB         │
                                        │   (Append-Only Versions & Runs)     │
                                        └─────────────────────────────────────┘
```

---

## 3. Technology Stack

- **Frontend:** React 19, TypeScript, Vite 8, Tailwind CSS v4, React Router 7.
- **Typography & Theme:** Lora (serif), Source Sans 3 (sans-serif), warm ivory/parchment palette (`#F4EFE5`, `#E4D8C6`, `#302B26`, `#53675C`, `#A65F48`).
- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2, Pydantic v2, Psycopg 3.
- **Database:** PostgreSQL (Supabase with connection pooler). Local tests run in-memory SQLite with foreign keys enabled.
- **AI Integration:** Google GenAI SDK (`gemini-2.5-flash` with structured schema and fallback).
- **Deployment:** Vercel (frontend), Render (backend).

---

## 4. Demo Brand: LumaCare

The platform includes a pre-configured demo brand workspace, **LumaCare**, with the following approved brand knowledge:

| Code | Title / Type | Statement |
|---|---|---|
| `GUIDE-001` | Outcome Claim | Do not promise guaranteed medical or skincare outcomes. |
| `GUIDE-002` | Brand Tone | Use friendly, reassuring and realistic messaging. |
| `GUIDE-003` | Consistency | Claims must be consistent with approved product information. |
| `FACT-001` | Approved Fact | The product is designed to support clearer-looking skin. |
| `FACT-002` | Approved Fact | No guaranteed acne-removal timeframe has been approved. |
| `TERM-001` | Preferred Term | "supports clearer-looking skin" |
| `TERM-001` | Prohibited Term | "guaranteed acne removal" |

---

## 5. Judge Evaluation Scenarios (1-Click Templates)

On the home workspace, judges can click any test scenario to test the full lifecycle:

1. **Test 1: Non-Compliant Ad Copy**
   - *Content:* `"Our revolutionary cream guarantees 100% acne removal in just 2 days! Buy now and get flawless skin instantly."`
   - *Expected:* Status `non_compliant`. Detects prohibited term `"guarantees 100% acne removal"`, unapproved timeframe `"in just 2 days"` (against `FACT-002`), and exaggerated claim `"flawless skin instantly"`.
2. **Test 2: Compliant Social Post**
   - *Content:* `"Discover a simple addition to your skincare routine with LumaCare. Our cream is designed to support clearer-looking skin. Enjoy a gentle, reassuring approach to everyday skincare."`
   - *Expected:* Status `compliant`. Identifies preferred terminology, confirms reassuring tone, produces zero violations.
3. **Test 3: Partially Compliant Post**
   - *Content:* `"Make your skincare routine simpler with LumaCare. Our cream supports clearer-looking skin and helps reduce acne within 7 days. Experience a gentle approach to everyday skincare."`
   - *Expected:* Status `needs_review`. Flags unapproved 7-day acne reduction timeframe while preserving positive observations.

---

## 6. Local Development Setup

### Backend

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env

# Run all 87 automated tests:
pytest -v

# Start development server:
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run build
npm run dev
```

Visit `http://localhost:5173` to explore the workspace.

---

## 7. Public Deployment Guide

### A. Database (Supabase)
1. Create a free project on [Supabase](https://supabase.com).
2. Copy the **Session Pooler** connection string (Host: `aws-0-...pooler.supabase.com`, Port: `5432`).
3. Set `DATABASE_URL=postgresql+psycopg://postgres.PROJECT:PASSWORD@aws-0-...pooler.supabase.com:5432/postgres`.
4. Tables and the LumaCare demo brand are automatically initialized and seeded on first application startup (`create_all()` + idempotent seed).

### B. Backend (Render)
1. Create a new Web Service on [Render](https://render.com) connected to this repository (or use the blueprint in `render.yaml`).
2. Set Environment Variables:
   - `DATABASE_URL`: Your Supabase pooler connection string.
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `GEMINI_MODEL`: `gemini-2.5-flash`
   - `CORS_ORIGINS`: `https://YOUR-APP.vercel.app,http://localhost:5173`
   - `PYTHON_VERSION`: `3.13.0`
3. Health check path: `/health`

### C. Frontend (Vercel)
1. Import repository on [Vercel](https://vercel.com) with root directory set to `frontend`.
2. Framework Preset: `Vite`.
3. Set Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-backend.onrender.com`
4. Deploy. Vercel SPA routing is pre-configured via `frontend/vercel.json`.

---

## 8. License

MIT License. Designed and developed for Round 2 Hackathon Submission.
