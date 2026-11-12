# Inkloom AI — Intelligent Multi-Brand Brand-Governance Platform

> **Round 3 Final Master Implementation & Acceptance Package**  
> Evaluates submitted marketing, promotional, and communication content against a brand's approved guidelines, facts, terminology, visual identity, and voice. It produces explainable findings, visual compliance reports, and suggested corrections while preserving human authority over final approval.

[![Backend Tests](https://img.shields.io/badge/pytest-169%20passed-success?logo=pytest&logoColor=white)](backend/tests)
[![Frontend Tests](https://img.shields.io/badge/node%20test-8%20passed-success?logo=nodedotjs&logoColor=white)](frontend/test/auth_logout.test.ts)
[![TypeScript](https://img.shields.io/badge/typescript-strict%20clean-blue?logo=typescript&logoColor=white)](frontend/tsconfig.json)
[![React 19](https://img.shields.io/badge/react-19.3.1-61DAFB?logo=react&logoColor=black)](frontend/package.json)
[![FastAPI](https://img.shields.io/badge/fastapi-0.162.0-009688?logo=fastapi&logoColor=white)](backend/requirements.txt)
[![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)](backend/requirements.txt)

---

## Live Production Deployments & Links

| Service | URL | Notes |
|---|---|---|
| **Production Web Application** | [https://inkloom-ai-wheat.vercel.app](https://inkloom-ai-wheat.vercel.app) | React 19 SPA hosted on Vercel with responsive public landing & multi-brand workspace. |
| **Backend API Health Check** | [https://inkloom-backend-upau.onrender.com/health](https://inkloom-backend-upau.onrender.com/health) | FastAPI health probe returning system status, DB pool state, and Gemini readiness. |
| **Interactive API Documentation** | [https://inkloom-backend-upau.onrender.com/docs](https://inkloom-backend-upau.onrender.com/docs) | Interactive Swagger UI for all 31 endpoints with schema definitions and test runner. |
| **ReDoc API Specifications** | [https://inkloom-backend-upau.onrender.com/redoc](https://inkloom-backend-upau.onrender.com/redoc) | Clean, searchable OpenAPI specifications for developers and integrators. |
| **GitHub Repository** | [https://github.com/shatakshi-rawat-130613/inkloom-ai](https://github.com/shatakshi-rawat-130613/inkloom-ai) | Official `main` branch containing all Round 3 source code, tests, and migrations. |

---

## Table of Contents

1. [Executive Summary & Round 3 Achievements](#1-executive-summary--round-3-achievements)
2. [System Architecture & Technology Stack](#2-system-architecture--technology-stack)
3. [The 3 Core Round 3 Commitments: In-Depth Breakdown](#3-the-3-core-round-3-commitments-in-depth-breakdown)
   - [Improvement 1: Multi-Brand Management, Organisation Isolation & RBAC](#improvement-1-multi-brand-management-organisation-isolation--rbac)
   - [Improvement 2: Multimodal Document Ingestion & Genuine Visual Brand Verification](#improvement-2-multimodal-document-ingestion--genuine-visual-brand-verification)
   - [Improvement 3: Claim-Level Evidence Grounding, Immutable Versions & Auditability](#improvement-3-claim-level-evidence-grounding-immutable-versions--auditability)
4. [Complete Local Developer Setup Guide](#4-complete-local-developer-setup-guide)
   - [Prerequisites](#prerequisites)
   - [Step 1: Clone Repository](#step-1-clone-repository)
   - [Step 2: Backend Setup & Virtual Environment](#step-2-backend-setup--virtual-environment)
   - [Step 3: Database Initialization & Migrations](#step-3-database-initialization--migrations)
   - [Step 4: Start Backend Server](#step-4-start-backend-server)
   - [Step 5: Frontend Setup & Dev Server](#step-5-frontend-setup--dev-server)
5. [Complete Environment Variable Reference](#5-complete-environment-variable-reference)
6. [Testing & Quality Assurance Guide](#6-testing--quality-assurance-guide)
   - [Running Backend Pytest Suite (169 Tests)](#running-backend-pytest-suite-169-tests)
   - [Contract Parity Verification](#contract-parity-verification)
   - [Running Frontend Regression Suite (8 Tests)](#running-frontend-regression-suite-8-tests)
   - [Frontend Linting & TypeScript Build](#frontend-linting--typescript-build)
   - [Automated Live Production Acceptance Audits](#automated-live-production-acceptance-audits)
7. [API Endpoints Reference](#7-api-endpoints-reference)
8. [Demo Access & Evaluation Workflow](#8-demo-access--evaluation-workflow)
9. [Troubleshooting & Common Pitfalls](#9-troubleshooting--common-pitfalls)
10. [Known Limitations & Future Roadmap](#10-known-limitations--future-roadmap)
11. [License](#11-license)

---

## 1. Executive Summary & Round 3 Achievements

In Round 3 (the Final Round), Inkloom AI was transformed from a single-brand compliance checker into an **enterprise-ready, multi-brand brand-governance platform**. 

All three major commitments for Round 3 have been completely implemented, verified on the live production stack (Render + Supabase + Vercel), and backed by a comprehensive suite of **169 passing backend tests** and zero-warning TypeScript checks:

1. **Multi-Brand Management & Tenant Isolation**:
   - Independent organisation self-registration with automatic initial Brand Manager (`admin`) role provisioning.
   - Dynamic multi-brand workspaces with strictly isolated compliance guidelines, verified factual statements, preferred and prohibited terminology, and visual identity assets.
   - Granular Role-Based Access Control (RBAC) separating **Brand Managers (`admin`)**, **Content Creators (`editor`)**, and **Compliance Auditors (`reviewer`)**.
   - Cryptographically enforced tenant isolation preventing cross-tenant reads or writes (returning standard `404 Not Found` responses to prevent resource existence disclosure).

2. **Multimodal Document Ingestion & Genuine Visual Brand Verification**:
   - Universal ingestion of Word documents (`.docx`), native text PDFs, scanned image-only PDFs, plain text (`.txt`), markdown (`.md`), and promotional images (`.png`, `.jpg`, `.jpeg`, `.webp`) up to 10MB via `POST /api/documents/extract`.
   - Two-tier PDF processing with automated fallback to multimodal vision OCR for scanned image pages, tagging `source="ocr"`.
   - **Genuine Visual Logo Verification** comparing uploaded graphics against approved brand logo specifications across 4 distinct states:
     - `APPROVED_LOGO_DETECTED` (authentic brand mark confirmed with matching geometry and palette).
     - `POSSIBLE_INCORRECT_LOGO` (distorted, unapproved variant, or competing brand logo detected).
     - `EXPECTED_LOGO_NOT_DETECTED` (promotional creative missing expected brand mark).
     - `UNABLE_TO_DETERMINE` (obscured, cropped, or ambiguous image preventing conclusive determination).
   - Dominant color palette extraction using K-Means clustering with Euclidean and CIELAB $\Delta E$ distance matching against approved brand swatches.
   - Sensitive credential and secret scanning detecting OAuth client secrets, API keys, private keys, and database connection URIs, redacting them from logs/previews and enforcing human review.

3. **Claim-Level Grounding, Immutable Versions & Audit History**:
   - Hybrid analysis pipeline combining compiled deterministic rule checks with Google Gemini structured JSON inference (local default: `gemini-3.8-flash`; production: `gemini-3.6-flash`; high-availability fallback: `gemini-3.1-flash-lite`).
   - Strict grounding verification: every flagged finding must reference valid server-side guidelines or approved facts; ungrounded citations or quotes missing from source text are rejected or downgraded.
   - Immutable versioning model (`v1`, `v2`, `v3`...): revisions create new snapshots while preserving every prior version, run, and finding.
   - `knowledge_snapshot` preservation: every analysis run records the exact guidelines, facts, and terms active at that moment, providing verifiable historical auditability even as brand guidelines evolve.
   - Chronological, append-only audit trail (`audit_logs`) tracking actor, entity, action, and timestamp.
   - Complete human review workflow: submission for review, approvals, rejections with mandatory comments, and revision requests.

---

## 2. System Architecture & Technology Stack

Inkloom AI is engineered as a **modular monolith with a hybrid deterministic and multimodal AI pipeline**. The architecture prioritizes auditability, predictability, and defensibility by enforcing deterministic validation over raw model outputs.

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React 19 + TypeScript + Vite)"]
        Landing["Public Landing Page (Pod.ai IA, Smooth Hash Nav)"]
        AuthUI["Split Login & Org Lookup (Demo Role Launcher)"]
        Workspace["Multi-Brand Workspace (Manager / Creator / Auditor)"]
    end

    subgraph Gateway["FastAPI Application (Python 3.13)"]
        Router["API Router (31 Endpoints)"]
        AuthMW["JWT Authentication & RBAC Middleware"]
        TenantISO["Tenant Scoping & Multi-Tenancy Boundary"]
    end

    subgraph Services["Core Application Services"]
        DocExtract["Document Extraction & Vision Service"]
        RuleEngine["Deterministic Rule Engine & Secret Scanner"]
        GeminiService["Gemini Multimodal Analyzer (3.8 Flash dev / 3.6 Flash prod / 3.1 Flash-Lite fallback)"]
        Grounding["Grounding Validator & Reference Verifier"]
        Workflow["Submission & Versioning Lifecycle Service"]
    end

    subgraph DataStore["Data Layer (PostgreSQL / SQLite)"]
        Alembic["Alembic Migrations: 001_initial_schema & 002_add_auth_and_visual_assets (head)"]
        Tables[("Organisations, Users, Brands, Guidelines, Facts, Terms, Assets, Submissions, Versions, Runs, Reviews, Audit Logs")]
    end

    Client -->|REST JSON + Multipart| Router
    Router --> AuthMW
    AuthMW --> TenantISO
    TenantISO --> DocExtract
    TenantISO --> Workflow

    DocExtract -->|Native & Scanned Fallback OCR| GeminiService
    DocExtract -->|Perceptual Hash & Color Palette| RuleEngine

    Workflow --> RuleEngine
    Workflow --> GeminiService

    RuleEngine -->|Merge & Deduplicate| Grounding
    GeminiService -->|Structured JSON Output| Grounding

    Grounding -->|Deterministic Status Policy| Workflow
    Workflow --> Tables
    Alembic -.->|Schema Versioning| Tables
```

### Technology Stack Matrix

| Layer | Technology | Version | Purpose & Rationale |
|---|---|---|---|
| **Frontend Framework** | React | `19.3.1` | Next-generation React with modern concurrency and fast state transitions. |
| **Routing** | React Router DOM | `7.18.5` | Route-aware navigation with smooth hash-scrolling (`/#platform`, `/#solutions`, etc.) and brand routing. |
| **Styling** | Tailwind CSS & Vite Plugin | `4.3.4` | Ultra-fast utility styling using Inkloom's warm editorial palette (Ivory `#FDFBF7`, Parchment `#F4EFE6`, Deep Ink `#1C1917`, Sage `#3B5E4F`, Terracotta `#9C4132`). |
| **Typography** | Fontsource (Lora & Source Sans 3) | `5.3.x` | Self-hosted serif and sans-serif fonts matching high-end editorial brand guidelines. |
| **Build Tool** | Vite | `8.3.5` | Lightning-fast development server and optimized ESM production bundling. |
| **Type System** | TypeScript | `5.9.3` | Strict type checking with 100% contract parity against backend Pydantic models. |
| **Backend Framework** | FastAPI | `0.162.0` | High-performance asynchronous Python API with automatic OpenAPI 3.1 generation. |
| **Python Runtime** | CPython | `3.13.x` | Latest stable Python runtime with improved performance and modern typing. |
| **Data Validation** | Pydantic & Pydantic-Settings | `2.14.2` | Strict data schema enforcement, request validation, and environment configuration. |
| **Database ORM** | SQLAlchemy | `2.1.8` | Declarative 2.0-style database models with connection pooling and typed sessions. |
| **Database Migrations** | Alembic | `1.20.1` | Versioned, additive migrations preserving historical records without schema resets. |
| **PostgreSQL Driver** | Psycopg 3 Binary | `3.3.8` | Modern async/sync PostgreSQL driver with Supabase session pooler support. |
| **Authentication** | PyJWT & Bcrypt | `2.15.1` / `5.0.0` | Secure password hashing (`bcrypt`) and signed JWT access tokens (`HS256`). |
| **Multimodal AI** | Google GenAI SDK | `2.34.0` | Official SDK communicating with Google Gemini (`gemini-3.8-flash` local default, `gemini-3.6-flash` production, `gemini-3.1-flash-lite` fallback) with structured JSON schemas and vision OCR. |
| **Document Processing** | PyPDF & Python-Multipart | `7.0.1` / `0.0.33` | Stream text extraction, scanned page image extraction, and multipart file uploads. |
| **Image Processing** | Pillow (PIL) | `13.0.0` | Image format conversion, raster manipulation, perceptual dHash calculation, and color extraction. |
| **Testing** | Pytest & HTTPX | `9.2.0` / `0.28.1` | 169 unit, integration, contract parity, and security regression tests. |

---

## 3. The 3 Core Round 3 Commitments: In-Depth Breakdown

### Improvement 1: Multi-Brand Management, Organisation Isolation & RBAC

- **Enterprise Organisation Multi-Tenancy**:
  - Independent organisation self-registration (`POST /api/auth/register`).
  - Registering creates the organisation record and provisions the initial user as its **Brand Manager (`admin`)**.
  - Subsequent users can register into an existing organisation or be invited by a Brand Manager (`POST /api/auth/members`).
- **Dynamic Multi-Brand Workspaces**:
  - Brand Managers can create multiple brands within their organisation (e.g. LumaCare skincare, Harvest & Hearth organic foods, Finora fintech).
  - Each brand maintains isolated brand knowledge:
    - **Compliance Guidelines**: code, title, category, rule text, default severity (`critical`, `high`, `medium`, `low`, `info`).
    - **Approved Factual Statements**: code, claim statement, scientific/legal source.
    - **Terminology Rules**: code, preferred term, prohibited term, notes.
    - **Visual Brand Assets**: asset name, asset type (`logo`, `palette`, `typography`, `imagery`), image URL or SVG, logo specifications, primary hex colors.
- **Strict 3-Tier Role-Based Access Control (RBAC)**:
  - **Brand Manager (`admin`)**: Enforced at the route level via FastAPI dependency `Depends(require_admin)` for brand creation, profile updates, guideline/fact/term/asset mutations, and team member provisioning (`POST /api/auth/members`). Also possesses full review authority.
  - **Content Creator (`editor`)**: Authorized to create submissions, upload marketing creative, generate new content versions, run compliance analyses, and request review. Service-level checks in `record_review` block creators from reviewing their own submissions (`403 Forbidden`), and route-level dependencies block mutating brand knowledge (`403 Forbidden`).
  - **Compliance Auditor (`reviewer`)**: Authorized to review analyzed submissions, inspect claim grounding, and record authoritative human review verdicts (`approved`, `rejected`, `revisions_requested`). Service-level checks in `request_review` prevent reviewers from submitting content for review (`403 Forbidden`), and route-level dependencies block modifying brand knowledge (`403 Forbidden`).
- **Cryptographic Tenant Isolation**:
  - All database queries for brands, guidelines, facts, assets, submissions, and audit logs are strictly scoped by `organisation_id`.
  - Attempts to access resources outside the authenticated user's organisation return `404 Not Found` (never leaking resource existence or IDs).
- **Alembic Schema Evolution & Migration History**:
  - `001_initial_schema`: Initial multi-tenant baseline migration creating tables for `organisations`, `users`, `brands`, `guidelines`, `factual_statements`, `terminology_rules`, `submissions`, `submission_versions`, `analysis_runs`, `review_records`, and `audit_logs`.
  - `002_add_auth_and_visual_assets`: Additive schema revision introducing `password_hash` and `is_active` to `users`, `brand_assets` (supporting logos, color palettes, and brand guidelines metadata), and `document_extractions` (storing multimodal extraction and OCR artifacts). Confirmed as the current Alembic head revision (`002_add_auth_and_visual_assets`).
  - **Automated Startup Migration & Zero-Downtime Synchronization**: `init_db()` in `backend/app/db.py` inspects existing database tables on startup, automatically stamps `001_initial_schema` if unversioned tables exist, and executes `command.upgrade(alembic_cfg, "head")` to ensure that both cloud PostgreSQL (Supabase / Render) and local SQLite instances are always synchronized at head without manual intervention or data loss.

---

### Improvement 2: Multimodal Document Ingestion & Genuine Visual Brand Verification

- **Universal Document Ingestion (`POST /api/documents/extract`)**:
  - Ingests Word documents (`.docx`), native text PDFs (`.pdf`), scanned image-only PDFs (`.pdf`), plain text (`.txt`), markdown (`.md`), and images (`.png`, `.jpg`, `.jpeg`, `.webp`) up to 10MB.
  - Returns extracted text, detected document type, word count, line count, character count, page count, and source tagging (`native` vs `ocr`).
- **Two-Tier PDF Extraction with Vision OCR Fallback**:
  - *Tier 1 (Native)*: Extracts structural text streams using `pypdf`.
  - *Tier 2 (Scanned Fallback)*: When native text length is below the readability threshold (< 40 characters), automatically extracts embedded page raster images and runs Gemini Multimodal Vision OCR, tagging `source="ocr"`.
- **Genuine Visual Logo Verification**:
  - Evaluates uploaded visual marketing creatives against approved brand logo specifications (including wordmark text, acceptable variants, and expected primary color).
  - Multimodal Gemini Vision inspects the image and returns one of 4 standardized states with confidence score and qualitative explanation:
    1. `APPROVED_LOGO_DETECTED`: Authentic brand mark or wordmark clearly visible with matching colors and geometry.
    2. `POSSIBLE_INCORRECT_LOGO`: Altered, distorted, unapproved variant, or competitor brand logo detected.
    3. `EXPECTED_LOGO_NOT_DETECTED`: Missing brand mark on promotional marketing creative.
    4. `UNABLE_TO_DETERMINE`: Obscured, low-resolution, or cropped image preventing conclusive verification.
  - Secondary fallback using 64-bit difference perceptual hashing (`dHash`) with Hamming distance comparison (distance $\le 6$ indicates match; distance $> 22$ indicates significant divergence).
- **Dominant Color Palette Extraction & Compliance**:
  - Quantizes image colors using K-Means clustering in RGB space.
  - Computes Euclidean distance and CIELAB $\Delta E$ against approved brand palette swatches.
  - Generates `visual` category findings if primary colors diverge or if resolution is below brand minimums.
- **Sensitive Credential & Secret Scanner**:
  - Proactively detects OAuth client secrets, API keys, private keys, database URIs, and passwords in uploaded copy.
  - Automatically redacts sensitive values from logs, previews, and findings.
  - Returns an explicit high-severity finding and forces `overall_status = "needs_review"`.

---

### Improvement 3: Claim-Level Evidence Grounding, Immutable Versions & Auditability

- **Hybrid Deterministic & Multimodal Analysis Pipeline**:
  - **Deterministic Rule Engine**: Fast, compiled regular expression patterns catch known prohibited terminology, missing disclaimers, sensitive credentials, and exact phrase violations before AI evaluation, backed by dedicated regression test suites.
  - **Gemini Multimodal Analyzer**: Evaluates tone, claim validity, competitor comparisons, and qualitative nuance using strict JSON schema output (`response_schema`). Uses local default `gemini-3.8-flash`, production model `gemini-3.6-flash`, and high-availability fallback `gemini-3.1-flash-lite` (with standalone deterministic rule-engine completion if AI services are unavailable or unconfigured).
  - **Grounding Validator**: Model-generated citations are cross-referenced against server-side guidelines and approved facts. Fabricated guidelines or facts are stripped; quotes not present in the source text are downgraded.
- **Immutable Revision Lifecycle**:
  - Submissions follow an append-only revision tree (`v1`, `v2`, `v3`...).
  - Editing content creates a new version snapshot while permanently preserving prior versions, runs, and findings.
- **Permanent Knowledge Snapshotting**:
  - Every analysis run records an immutable `knowledge_snapshot` containing the exact active guidelines, facts, and terms active at that moment.
  - Preserves historical explainability even if guidelines or facts evolve later.
- **Human Sovereign Authority**:
  - The AI analysis engine only provides decision support.
  - Authoritative status decisions (`approved`, `rejected`, `revisions_requested`) require an authorized human Compliance Auditor.
  - Rejections and revision requests require explanatory comments; approving non-compliant content is permitted (human authority) but requires mandatory justifications recorded in the audit trail.
- **Chronological Append-Only Audit Trail**:
  - Every lifecycle event (`submission_created`, `version_created`, `analysis_completed`, `review_requested`, `review_recorded`) is written to `audit_logs` with actor ID, entity ID, action, and timestamp.

---

## 4. Complete Local Developer Setup Guide

Follow these exact, verified commands on macOS or Linux to run Inkloom AI locally from scratch.

### Prerequisites

- **Python 3.13+** (recommended: Python 3.13 via pyenv or Homebrew)
- **Node.js 20+** and **npm**
- **Git**
- *(Optional)* **PostgreSQL** (if omitted, the system automatically uses local SQLite)
- *(Optional)* **Google Gemini API Key** (if omitted, the deterministic rule engine runs completely with `ai_status="disabled"`)

---

### Step 1: Clone Repository

```bash
git clone https://github.com/shatakshi-rawat-130613/inkloom-ai.git
cd inkloom-ai
```

---

### Step 2: Backend Setup & Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3.13 -m venv .venv

# Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Upgrade pip and install all required dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3: Database Initialization & Migrations

Inkloom AI supports both **PostgreSQL** and zero-configuration **SQLite**.

#### Option A: Local SQLite (Fastest, Zero External Dependencies)
By default, if `DATABASE_URL` is omitted, Inkloom AI connects to `sqlite:///./inkloom_dev.db`.

```bash
# Create local .env file in backend/ (git-ignored)
# Choose your own private local demo password for DEMO_SEED_PASSWORD
cat << 'EOF' > .env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./inkloom_dev.db
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
CORS_ORIGINS=http://localhost:5173
# In development, leave JWT_SECRET_KEY empty to auto-generate a safe random secret per process
JWT_SECRET_KEY=
# DEMO_SEED_PASSWORD is required when running python -m app.seed to seed demo accounts.
# Set any local password of your choice:
DEMO_SEED_PASSWORD=YourLocalDevPassword123!
EOF

# Run database schema migrations (executes Alembic upgrade to head)
python -c "from app.db import init_db; init_db()"

# (Optional) Verify migration revision via Alembic CLI (head: 002_add_auth_and_visual_assets)
alembic current

# Seed demo brand (LumaCare) and demo users using your configured local password
python -m app.seed
```

#### Option B: PostgreSQL (Supabase / Local Postgres)
If you have a PostgreSQL database running:

```bash
# Set your PostgreSQL connection string in backend/.env:
# Note: Use postgresql+psycopg:// to use the modern psycopg 3 driver
cat << 'EOF' > .env
ENVIRONMENT=development
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/inkloom
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
CORS_ORIGINS=http://localhost:5173
JWT_SECRET_KEY=
DEMO_SEED_PASSWORD=YourLocalDevPassword123!
EOF

# Run database schema migrations (executes Alembic upgrade to head)
python -c "from app.db import init_db; init_db()"

# (Optional) Verify migration revision via Alembic CLI (head: 002_add_auth_and_visual_assets)
alembic current

# Seed demo data
python -m app.seed
```

---

### Step 4: Start Backend Server

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Start Uvicorn development server on port 8000
uvicorn app.main:app --reload --port 8000
```

Verify backend health in your terminal or browser:
```bash
curl http://localhost:8000/health
# Response: {"status":"ok","database":"connected","ai_status":"enabled"} (or "disabled" if no Gemini key)
```
Interactive API docs are now available at: **http://localhost:8000/docs**

---

### Step 5: Frontend Setup & Dev Server

Open a new terminal window:

```bash
cd inkloom-ai/frontend

# Install frontend dependencies
npm install

# (Optional) Create local env file in frontend/ (git-ignored)
# VITE_DEMO_SEED_PASSWORD is for local development convenience ONLY.
# It should match the DEMO_SEED_PASSWORD set in backend/.env.
cat << 'EOF' > .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_DEMO_SEED_PASSWORD=YourLocalDevPassword123!
EOF

# Start Vite development server
npm run dev
```

> [!WARNING] VITE Environment Variable Security
> Any variable prefixed with `VITE_` (such as `VITE_DEMO_SEED_PASSWORD`) is statically baked into client-side JavaScript during `vite build` and is visible to any browser inspecting the application.
> - **Only configure `VITE_DEMO_SEED_PASSWORD` in local development (`frontend/.env.local`).**
> - **NEVER set `VITE_DEMO_SEED_PASSWORD` in production hosting environments (e.g. Vercel).**
> - In production, users enter their credentials directly or register their own organisations.

Open your browser at **http://localhost:5173**.  
You can explore the public landing page, click **Login** or **Demo Login**, and access the multi-brand workspace.

---

## 5. Complete Environment Variable Reference

Inkloom AI uses typed environment configuration via Pydantic Settings (`backend/app/config.py`) and Vite environment variables (`frontend/src/api/client.ts`).

### Backend Environment Variables (`backend/.env`)

| Variable | Type | Required? | Default / Fallback | Description & Safe Sample Value |
|---|---|---|---|---|
| `ENVIRONMENT` | `string` | **No** | `development` | Runtime mode: `development`, `test`, or `production`. In production, strict security validations are enforced on `JWT_SECRET_KEY`. |
| `DATABASE_URL` | `string` | **No** | `sqlite:///./inkloom_dev.db` | Database connection string. For PostgreSQL, use `postgresql+psycopg://user:pass@host:5432/dbname`. For SQLite, use `sqlite:///./inkloom_dev.db`. |
| `GEMINI_API_KEY` | `string` | **No** | `None` | Google Gemini API key. If omitted, AI analysis is disabled (`ai_status="disabled"`), and the deterministic rule engine runs standalone. |
| `GEMINI_MODEL` | `string` | **No** | `gemini-3.8-flash` | Primary Gemini model ID. Local development defaults to `gemini-3.8-flash` (defined in `backend/app/config.py`). Live Render production is configured with `gemini-3.6-flash`. The analysis and vision services automatically fall back to `gemini-3.1-flash-lite` on transient 503 or quota exhaustion. |
| `GEMINI_TIMEOUT_SECONDS` | `float` | **No** | `30.0` | Timeout in seconds for external Gemini API calls before triggering fallback or timing out. |
| `CORS_ORIGINS` | `string` | **No** | `http://localhost:5173,https://inkloom-ai-wheat.vercel.app` | Comma-separated list of allowed frontend origins for CORS headers. Regex `^https:\/\/.*\.vercel\.app$` is also permitted. |
| `JWT_SECRET_KEY` | `string` | **In Production** | Auto-generated random in dev | Cryptographic secret key used to sign and verify session JWTs using HMAC-SHA256 (`HS256`). In production, this **must** be an independently generated strong secret of $\ge 32$ characters. Known static development defaults are strictly blocked. Generate with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`. |
| `JWT_ALGORITHM` | `string` | **No** | `HS256` | JWT signing algorithm. Standard: `HS256`. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | **No** | `10080` (7 days) | Token expiration duration in minutes. |
| `DEMO_SEED_PASSWORD` | `string` | **When Seeding** | `""` (no default) | Password assigned to demo users when running `python -m app.seed`. Fails with a clear error if missing during seeding; no password is ever printed. |
| `MAX_CONTENT_CHARS` | `int` | **No** | `10000` | Maximum character length for a single content submission version. |
| `ANALYZE_RATE_LIMIT_PER_MINUTE` | `int` | **No** | `10` | Maximum compliance analysis requests per minute per client IP. |

### Frontend Environment Variables (`frontend/.env.local`)

| Variable | Type | Required? | Default / Fallback | Description & Safe Sample Value |
|---|---|---|---|---|
| `VITE_API_BASE_URL` | `string` | **No** | `""` (relative root) | Base URL for FastAPI backend. In local development: `http://localhost:8000`. In production: left empty (relative) or set to the Render backend URL. |
| `VITE_DEMO_SEED_PASSWORD` | `string` | **Dev Only** | `""` | Local development helper for pre-filling demo login buttons. **Never set in production builds (e.g. Vercel) because VITE variables are exposed in browser JavaScript bundles.** |

> [!SECURITY NOTE]  
> Never commit `.env` or `.env.local` files containing real production secrets. Both files are included in `.gitignore`.

---

## 6. Testing & Quality Assurance Guide

Inkloom AI enforces high software quality standards through automated contract testing, unit testing, security regression suites, and static analysis.

### Running Backend Pytest Suite (169 Tests)

Ensure your virtual environment is active in the `backend/` directory:

```bash
cd backend
source .venv/bin/activate

# Run all 169 automated tests with verbose output
pytest -v
```

All 169 tests pass in ~21 seconds:

```
======================= 169 passed, 1 warning in 20.80s ========================
```

#### Running Specific Test Suites

```bash
# Security configuration & credential validation tests
pytest tests/test_security_configuration.py -v

# Secret scanner & redaction tests (OAuth, API keys, private keys)
pytest tests/test_security_scanner.py -v

# Strict multi-tenant isolation tests (404 on cross-tenant read/write)
pytest tests/test_multi_tenant_isolation.py -v

# Role-based access control (RBAC) tests (admin vs creator vs reviewer)
pytest tests/test_auth_and_rbac.py -v

# Multimodal document ingestion & logo verification tests
pytest tests/test_document_service.py -v

# Grounding, citation validation & status policy tests
pytest tests/test_validation.py -v

# Brand relevance & competitor context tests
pytest tests/test_brand_relevance.py -v
```

---

### Contract Parity Verification

To prevent schema drift between backend Pydantic models and frontend TypeScript interfaces, Inkloom AI includes an automated contract parity assertion:

```bash
pytest tests/test_contract_parity.py -v
```
This test inspects `backend/app/schemas.py` and `frontend/src/api/types.ts` to assert that all enum values, interfaces, and field names match 100%.

---

### Running Frontend Regression Suite (8 Tests)

Inkloom AI includes a comprehensive 8-scenario automated authentication and logout regression test suite verifying state clearance, navigation redirection, browser history replacement, and 401 interceptor handling:

```bash
cd frontend
npm test
```

Expected output:
```
▶ Full 8-Scenario Authentication & Logout Regression Suite
  ✔ Scenario 1: Brand Manager logs in -> opens /workspace -> logs out -> redirected to /login with replace: true
  ✔ Scenario 2: Content Creator logs in -> opens /submissions/:id -> logs out -> redirected to /login
  ✔ Scenario 3: Compliance Auditor logs in -> opens review page -> logs out -> redirected to /login
  ✔ Scenario 4: After logout, browser Back button does not reveal protected content
  ✔ Scenario 5: Refreshing a protected URL after logout redirects to /login
  ✔ Scenario 6: Directly opening a protected URL in a new tab without authentication redirects to /login
  ✔ Scenario 7: Logging in as a different role after logout does not retain previous role state or permissions
  ✔ Scenario 8: Expired or 401 Unauthorized API response immediately triggers centralized logout and redirect
✔ Full 8-Scenario Authentication & Logout Regression Suite
ℹ tests 8
ℹ pass 8
ℹ fail 0
```

---

### Frontend Linting & TypeScript Build

```bash
cd frontend

# Run ESLint across all TypeScript and React files
npm run lint

# Run strict TypeScript compiler checks and Vite production build
npm run build
```
Both commands must exit with **code 0** and zero warnings.

---

### Automated Live Production Acceptance Audits

Inkloom AI provides standalone Python scripts that verify the live deployed application on Render and Supabase:

```bash
cd backend
source .venv/bin/activate

# Execute the 27-step live acceptance journey against production
python scripts/live_acceptance_audit.py

# Execute the multimodal OCR & logo verification gap-closure suite
python scripts/live_ocr_and_logo_gap_closure.py
```

---

## 7. API Endpoints Reference

The backend exposes **31 active REST endpoints** implementing a multi-layered security model that distinguishes public access, demo-compatible access, authenticated tenant-scoped access, and role-enforced operations:

### Security & Access Control Model

1. **Public Endpoints (Unauthenticated)**:
   - System health probes (`/health`, `/api/health`), self-registration (`/api/auth/register`), authentication (`/api/auth/login`), workspace prefix lookup (`/api/auth/organisations/lookup`), and document/OCR extraction (`/api/documents/extract`).
   - Require no `Authorization` header.

2. **Demo-Compatible & Tenant-Scoped Endpoints (`Depends(get_optional_user)`)**:
   - **Without a Bearer Token (Unauthenticated / Demo Mode)**: Operations are permitted **strictly and exclusively on the public demo brand (`is_demo=True`, e.g. LumaCare)**. Unauthenticated users cannot read, create, or modify content or rules belonging to any private organisation.
   - **With a Valid Bearer Token (Authenticated Mode)**: Scoped strictly to the caller's `organisation_id` (plus public demo brands). Attempting to query, view, analyze, or review submissions, brands, or assets of another organisation returns standard `404 Not Found` (preventing resource existence disclosure).

3. **Role-Enforced Operations**:
   - **Route-Level Dependency (`Depends(require_admin)`)**:
     - Enforces `current_user.role == UserRole.ADMIN` (Brand Manager). Non-admin callers receive `403 Forbidden`.
     - Required for: inviting team members (`POST /api/auth/members`), provisioning new brand workspaces (`POST /api/brands`), updating brand profiles (`PATCH /api/brands/{id}`), and adding/deleting compliance guidelines (`/guidelines`), approved facts (`/facts`), terminology rules (`/terms`), and visual brand assets (`/assets`).
   - **Service-Level RBAC Enforcement**:
     - `POST /api/submissions/{id}/review-request`: Permitted for Content Creators (`editor`) and Brand Managers (`admin`). Compliance Auditors (`reviewer`) attempting to request review receive `403 Forbidden`.
     - `POST /api/submissions/{id}/reviews`: Permitted for Compliance Auditors (`reviewer`) and Brand Managers (`admin`). Content Creators (`editor`) attempting to record review decisions receive `403 Forbidden`.

---

### System & Health (2 Endpoints)

| Method | Endpoint | Access Level | Authorization Enforcement | Description |
|---|---|---|---|---|
| `GET` | `/health` | Public | None | Root system health check (database connection & Gemini readiness). |
| `GET` | `/api/health` | Public | None | Namespaced API health check probe. |

### Authentication & Organisation Team Management (6 Endpoints)

| Method | Endpoint | Access Level | Authorization Enforcement | Description |
|---|---|---|---|---|
| `POST` | `/api/auth/register` | Public | None | Register a new organisation; provision initial user as Brand Manager (`admin`). |
| `POST` | `/api/auth/login` | Public | None | Authenticate with email/password; returns signed JWT Bearer token with claims (`sub`, `org_id`, `role`, `email`). |
| `GET` | `/api/auth/me` | Authenticated | `Depends(get_current_user)` | Retrieve current authenticated user profile, assigned role, and organisation. |
| `GET` | `/api/auth/members` | Authenticated | `Depends(get_current_user)` | List all team members belonging to the caller's organisation. |
| `POST` | `/api/auth/members` | Brand Manager (`admin`) | `Depends(require_admin)` | Invite / add a team member with role (`admin`, `editor`, `reviewer`) to caller's organisation. Returns 403 for non-admins. |
| `GET` | `/api/auth/organisations/lookup` | Public | None | Prefix search for organisation names and slugs without exposing user accounts or credentials. |

### Brand Workspaces & Knowledge Management (13 Endpoints)

| Method | Endpoint | Access Level | Authorization Enforcement | Description |
|---|---|---|---|---|
| `GET` | `/api/brands` | Demo / Authenticated | `Depends(get_optional_user)` | List accessible brands: returns public demo brand if unauthenticated; returns demo brand + caller's organisation brands if authenticated. |
| `POST` | `/api/brands` | Brand Manager (`admin`) | `Depends(require_admin)` | Create a new brand workspace within caller's organisation. Returns 403 for non-admins. |
| `GET` | `/api/brands/{identifier}` | Demo / Authenticated | `Depends(get_optional_user)` + `_verify_brand_access` | Retrieve brand details, guidelines, facts, terms, and assets by slug or UUID. Public for demo brand; returns 404 for cross-tenant access. |
| `PATCH` | `/api/brands/{brand_id}` | Brand Manager (`admin`) | `Depends(require_admin)` | Update brand name, industry, description, or voice summary. Returns 403 for non-admins or 404 for non-tenant brand. |
| `POST` | `/api/brands/{brand_id}/guidelines` | Brand Manager (`admin`) | `Depends(require_admin)` | Add a compliance guideline rule to the brand workspace. Returns 403 for non-admins. |
| `DELETE` | `/api/brands/{brand_id}/guidelines/{code}` | Brand Manager (`admin`) | `Depends(require_admin)` | Deactivate a compliance guideline by code. Returns 403 for non-admins. |
| `POST` | `/api/brands/{brand_id}/facts` | Brand Manager (`admin`) | `Depends(require_admin)` | Add an approved factual statement with source citation. Returns 403 for non-admins. |
| `DELETE` | `/api/brands/{brand_id}/facts/{code}` | Brand Manager (`admin`) | `Depends(require_admin)` | Deactivate an approved factual statement by code. Returns 403 for non-admins. |
| `POST` | `/api/brands/{brand_id}/terms` | Brand Manager (`admin`) | `Depends(require_admin)` | Add a preferred or prohibited terminology rule. Returns 403 for non-admins. |
| `DELETE` | `/api/brands/{brand_id}/terms/{code}` | Brand Manager (`admin`) | `Depends(require_admin)` | Deactivate a terminology rule by code. Returns 403 for non-admins. |
| `GET` | `/api/brands/{brand_id}/assets` | Demo / Authenticated | `Depends(get_optional_user)` + `_verify_brand_access` | List visual brand assets (logos, palettes) for brand. Public for demo brand; scoped to tenant for custom brands. |
| `POST` | `/api/brands/{brand_id}/assets` | Brand Manager (`admin`) | `Depends(require_admin)` | Add a visual brand asset (approved logo specs, color swatches). Returns 403 for non-admins. |
| `DELETE` | `/api/brands/{brand_id}/assets/{asset_id}` | Brand Manager (`admin`) | `Depends(require_admin)` | Deactivate a visual brand asset by UUID. Returns 403 for non-admins. |

### Document Extraction & Visual Analysis (1 Endpoint)

| Method | Endpoint | Access Level | Authorization Enforcement | Description |
|---|---|---|---|---|
| `POST` | `/api/documents/extract` | Public / Demo-Compatible | `Depends(get_optional_user)` | Multipart ingestion for Word (`.docx`), PDF, scanned PDF (OCR fallback), and promotional images (`.png`, `.jpg`). Returns extracted text, OCR metadata, and visual logo verification. |

### Content Submissions, Workflows & Reviews (8 Endpoints)

| Method | Endpoint | Access Level | Authorization Enforcement | Description |
|---|---|---|---|---|
| `GET` | `/api/submissions` | Demo / Authenticated | `Depends(get_optional_user)` + tenant filtering | List submissions for brand workspace. Public for demo brand; strictly scoped to caller's organisation for tenant brands. |
| `POST` | `/api/submissions` | Demo / Creator or Manager | `Depends(get_optional_user)` + `verify_brand_access` | Create a new submission draft and initial version `v1`. Permitted on demo brand; requires tenant membership on custom brands. |
| `GET` | `/api/submissions/{id}` | Demo / Authenticated | `Depends(get_optional_user)` + `verify_submission_access` | Retrieve full submission details, immutable version history, and analysis runs. Returns 404 for cross-tenant access. |
| `POST` | `/api/submissions/{id}/versions` | Demo / Creator or Manager | `Depends(get_optional_user)` + `verify_submission_access` | Create a new immutable content version snapshot (`v2`, `v3`...). |
| `POST` | `/api/submissions/{id}/analyze` | Demo / Creator or Manager | `Depends(get_optional_user)` + `verify_submission_access` | Run hybrid deterministic rule-engine and Gemini compliance analysis on the active version. |
| `POST` | `/api/submissions/{id}/review-request` | Creator (`editor`) or Manager (`admin`) | `Depends(get_optional_user)` + service-level check | Transition analyzed content to `in_review`. Auditors (`reviewer`) receive 403 Forbidden. |
| `POST` | `/api/submissions/{id}/reviews` | Auditor (`reviewer`) or Manager (`admin`) | `Depends(get_optional_user)` + service-level check | Record authoritative human review verdict (`approved`, `rejected`, `revisions_requested`). Content Creators (`editor`) receive 403 Forbidden. |
| `GET` | `/api/submissions/{id}/audit` | Demo / Authenticated | `Depends(get_optional_user)` + `verify_submission_access` | Retrieve complete chronological, append-only audit trail for submission. |

### Historical Analysis Runs (1 Endpoint)

| Method | Endpoint | Access Level | Authorization Enforcement | Description |
|---|---|---|---|---|
| `GET` | `/api/analysis-runs/{id}` | Demo / Authenticated | `Depends(get_optional_user)` + `verify_submission_access` | Retrieve complete findings, confidence scores, and immutable knowledge snapshot of a specific historical run. |

---

## 8. Demo Access & Evaluation Workflow

Inkloom AI includes pre-seeded demo accounts and one-click role switching on the live production web app:

### Option 1: Live Demo Role Launcher (Fastest Evaluation)
1. Visit the live login page at **[https://inkloom-ai-wheat.vercel.app/login](https://inkloom-ai-wheat.vercel.app/login)**.
2. Under **"Explore with live demo roles"**, click any of the 3 pre-configured role buttons:
   - **Brand Manager** (`admin@lumacare.demo`): Provision brands, configure guidelines, facts, terms, visual assets, and manage team members.
   - **Content Creator** (`editor@lumacare.demo`): Draft marketing copy, upload documents, trigger OCR, run compliance analysis, and request review.
   - **Compliance Auditor** (`reviewer@lumacare.demo`): Review submitted drafts, inspect claim grounding, and issue final review decisions.
3. The frontend authenticates through `POST /api/auth/login`, receives a signed JWT, dynamically queries `GET /api/brands` for the authenticated user's organisation, and automatically resolves and routes to the user's authorised brand workspace (or routes to `/select-brand` if the organisation has multiple brands, or `/create-brand` if none exist). It never hardcodes a global workspace.

### Option 2: Self-Registration (Test Multi-Tenancy)
1. On the login page, switch to the **Register** tab.
2. Enter your name, email, password, and a **Company Name** (e.g. "Acme Corp").
3. Click **Create Account**.
4. You are registered as the **Brand Manager (`admin`)** of your newly created organisation.
5. Create new brands, configure custom compliance rules, upload logos, and invite team members.

---

## 9. Troubleshooting & Common Pitfalls

### 1. `ModuleNotFoundError: No module named 'fastapi'` or `'bcrypt'`
- **Cause**: Command was run against the system Python rather than the virtual environment.
- **Solution**: Activate the virtual environment first (`source .venv/bin/activate`), or call the venv binary directly (`.venv/bin/python` or `.venv/bin/pytest`).

### 2. SQLite vs PostgreSQL Driver String
- **Cause**: Using standard `postgres://` or `postgresql://` without specifying psycopg 3.
- **Solution**: Inkloom's `build_engine` automatically normalizes URLs to `postgresql+psycopg://`. If connecting directly via custom scripts, always use:
  ```
  DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
  ```

### 3. Missing `DEMO_SEED_PASSWORD` During Seeding
- **Cause**: Running `python -m app.seed` without setting `DEMO_SEED_PASSWORD` in the environment.
- **Solution**: Set `DEMO_SEED_PASSWORD=YourLocalPassword` in your `backend/.env` file before executing the seed script.

### 4. Insecure `JWT_SECRET_KEY` in Production
- **Cause**: Deploying to production with an empty `JWT_SECRET_KEY`, a known default (such as `"inkloom-production-jwt-secret-key-do-not-share-32charsmin"`), or a secret shorter than 32 characters.
- **Solution**: Generate a strong secret with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'` and configure it in your production host environment (e.g. Render Dashboard).

### 5. Gemini API 429 Quota or Unavailable (503)
- **Behavior**: Inkloom AI is engineered for high availability and graceful fallback. If the configured primary model (`gemini-3.6-flash` in Render production or `gemini-3.8-flash` in local development) encounters a transient 503 error, the backend retries once after a 1.5s backoff, then automatically falls back to `gemini-3.1-flash-lite`. If no API key is provided, credentials fail, or external quotas are exhausted, the system marks `ai_status="disabled"` (or `"unavailable"`) and completes the full compliance analysis using the standalone deterministic rule engine.

### 6. CORS Errors During Local Development
- **Cause**: Local frontend runs on a port not listed in `CORS_ORIGINS`.
- **Solution**: Add your frontend origin (e.g. `http://localhost:5173`) to `CORS_ORIGINS` in `backend/.env`.

### 7. Render Free-Tier Cold Start
- **Behavior**: If the Render backend has been idle, the initial HTTP request may experience a 30-50 second cold-start delay while the container spins up. Subsequent requests respond in under 200ms.

---

## 10. Known Limitations & Future Roadmap

### Known Limitations
- **2D Planar Visual Analysis**: Visual logo verification compares against 2D reference specifications. It does not currently reconstruct 3D non-planar package curvature (e.g. cylindrical bottles).
- **Ingestion File Size Cap**: File uploads are capped at 10MB to maintain strict latency and memory boundaries in containerized serverless environments.
- **Render Free-Tier Spin-Down**: Free-tier instances spin down after 15 minutes of inactivity.

### Future Roadmap
- **Enterprise SSO / SAML 2.0**: Integration with Okta, Google Workspace, and Microsoft Entra ID.
- **Headless CI/CD Marketing Linter**: A CLI tool allowing marketing teams to run `inkloom lint ./campaign/` inside GitHub Actions or GitLab CI.
- **Direct Figma & Canva Integrations**: Real-time compliance checking inside design canvas plugins.
- **Cross-Border Multi-Lingual Governance**: Automated localization compliance checking across 30+ languages with regional regulatory adaptation.

---

## 11. License

This project is licensed under the **MIT License**.  
Developed for the **Inkloom AI Round 3 Final Submission**.
