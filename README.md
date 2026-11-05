# Inkloom AI

Inkloom AI is a brand-governance platform. It checks marketing and communication content against an organisation's approved guidelines, facts and terminology, explains each finding with evidence, and leaves the final decision to a human reviewer.

This repository is a hackathon MVP built around a fictional demo brand, LumaCare.

## Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.13, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL (Supabase) |
| AI | Google Gemini with structured JSON output, plus a deterministic rule engine |
| Hosting | Vercel (frontend), Render (backend) |

## Repository layout

```
frontend/   React single-page application
backend/    FastAPI service, rule engine, Gemini integration
docs/       API contract and schema notes
```

## Local development

### Backend

```bash
cd backend
python3.13 -m venv .venv          # already created
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env           # then fill in values locally
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

All variables are documented in [`.env.example`](.env.example). Secrets such as `GEMINI_API_KEY` and `DATABASE_URL` live only in the backend environment and are never committed.

## Status

Work in progress. See the project plan for phase status.
