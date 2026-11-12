# Inkloom AI — Intelligent Multi-Brand Brand-Governance Platform

> **Round 3 Final Master Implementation & Acceptance Package**  
> Evaluates submitted marketing, promotional, and communication content against a brand's approved guidelines, facts, terminology, visual identity, and voice. It produces explainable findings, visual compliance reports, and suggested corrections while preserving human authority over final approval.

[![Backend Tests](https://img.shields.io/badge/pytest-162%20passed-success?logo=pytest&logoColor=white)](file:///backend/tests)
[![TypeScript](https://img.shields.io/badge/typescript-strict%20clean-blue?logo=typescript&logoColor=white)](file:///frontend/tsconfig.json)
[![React 19](https://img.shields.io/badge/react-19.3.1-61DAFB?logo=react&logoColor=black)](file:///frontend/package.json)
[![FastAPI](https://img.shields.io/badge/fastapi-0.162.0-009688?logo=fastapi&logoColor=white)](file:///backend/requirements.txt)
[![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)](file:///backend/requirements.txt)

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
   - [Running Backend Pytest Suite (162 Tests)](#running-backend-pytest-suite-162-tests)
   - [Contract Parity Verification](#contract-parity-verification)
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

All three major commitments for Round 3 have been completely implemented, verified on the live production stack (Render + Supabase + Vercel), and backed by a comprehensive suite of **162 passing backend tests** and zero-warning TypeScript checks:

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
   - Deterministic rule engine combined with Google Gemini 3.6/3.8 Flash structured JSON inference.
   - Strict grounding verification: every flagged finding must reference valid server-side guidelines or approved facts; ungrounded citations or quotes missing from source text are rejected or downgraded.
   - Immutable versioning model (`v1`, `v2`, `v3`...): revisions create new snapshots while preserving every prior version, run, and finding.
   - `knowledge_snapshot` preservation: every analysis run records the exact guidelines, facts, and terms active at that moment, guaranteeing historical auditability even as brand guidelines evolve.
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
        GeminiService["Gemini 3.6/3.8 Flash Multimodal Analyzer"]
        Grounding["Grounding Validator & Reference Verifier"]
        Workflow["Submission & Versioning Lifecycle Service"]
    end

    subgraph DataStore["Data Layer (PostgreSQL / SQLite)"]
        Alembic["Alembic Versioned Migrations (001, 002)"]
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
| **Multimodal AI** | Google GenAI SDK | `2.34.0` | Official SDK communicating with Google Gemini 3.6/3.8 Flash with structured JSON schemas and vision OCR. |
| **Document Processing** | PyPDF & Python-Multipart | `7.0.1` / `0.0.33` | Stream text extraction, scanned page image extraction, and multipart file uploads. |
| **Image Processing** | Pillow (PIL) | `13.0.0` | Image format conversion, raster manipulation, perceptual dHash calculation, and color extraction. |
| **Testing** | Pytest & HTTPX | `9.2.0` / `0.28.1` | 162 unit, integration, contract parity, and security regression tests. |

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
  - **Brand Manager (`admin`)**: Full rights to create and update brands, manage guidelines/facts/terms/assets, and invite or manage team members.
  - **Content Creator (`editor`)**: Authorized to create submissions, upload marketing creative, generate new content versions, and initiate compliance analyses. Forbidden from mutating brand knowledge or altering team roles (`403 Forbidden`).
  - **Compliance Auditor (`reviewer`)**: Authorized to review analyzed submissions, issue authoritative governance verdicts (`approved`, `rejected`, `revisions_requested`) with mandatory feedback, and audit compliance logs.
- **Cryptographic Tenant Isolation**:
  - All database queries for brands, guidelines, facts, assets, submissions, and audit logs are strictly scoped by `organisation_id`.
  - Attempts to access resources outside the authenticated user's organisation return `404 Not Found` (never leaking resource existence or IDs).

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
  - **Deterministic Rule Engine**: High-speed regex checks guarantee zero false negatives for prohibited terminology, missing disclaimers, sensitive credentials, and exact phrase violations.
  - **Gemini 3.6/3.8 Flash Analyzer**: Evaluates tone, claim validity, competitor comparisons, and qualitative nuance using strict JSON schema output (`response_schema`).
  - **Grounding Validator**: Model-generated citations are cross-referenced against server-side guidelines and approved facts. Fabricated guidelines or facts are stripped; quotes not present in the source text are downgraded.
- **Immutable Revision Lifecycle**:
  - Submissions follow an append-only revision tree (`v1`, `v2`, `v3`...).
  - Editing content creates a new version snapshot while permanently preserving prior versions, runs, and findings.
- **Permanent Knowledge Snapshotting**:
  - Every analysis run records an immutable `knowledge_snapshot` containing the exact active guidelines, facts, and terms active at that moment.
  - Guarantees complete historical explainability even if guidelines or facts evolve later.
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
# Create local .env file in backend/
cat << 'EOF' > .env
DATABASE_URL=sqlite:///./inkloom_dev.db
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
CORS_ORIGINS=http://localhost:5173
JWT_SECRET_KEY=local-dev-secret-key-at-least-32-characters-long
DEMO_SEED_PASSWORD=LumaCareDemo2026!
EOF

# Run database schema migrations & create tables
python -c "from app.db import init_db; init_db()"

# Seed demo brand (LumaCare) and demo users
python -m app.seed
```

#### Option B: PostgreSQL (Supabase / Local Postgres)
If you have a PostgreSQL database running:

```bash
# Set your PostgreSQL connection string in backend/.env:
# Note: Use postgresql+psycopg:// to use the psycopg 3 driver
cat << 'EOF' > .env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/inkloom
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
CORS_ORIGINS=http://localhost:5173
JWT_SECRET_KEY=local-dev-secret-key-at-least-32-characters-long
DEMO_SEED_PASSWORD=LumaCareDemo2026!
EOF

# Run database schema migrations
python -c "from app.db import init_db; init_db()"

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

# (Optional) Create local env file to point to your local FastAPI backend
cat << 'EOF' > .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_DEMO_SEED_PASSWORD=LumaCareDemo2026!
EOF

# Start Vite development server
npm run dev
```

Open your browser at **http://localhost:5173**.  
You can explore the public landing page, click **Login** or **Demo Login**, and access the multi-brand workspace.

---

## 5. Complete Environment Variable Reference

Inkloom AI uses typed environment configuration via Pydantic Settings (`backend/app/config.py`) and Vite environment variables (`frontend/src/api/client.ts`).

### Backend Environment Variables (`backend/.env`)

| Variable | Type | Required? | Default / Fallback | Description & Safe Sample Value |
|---|---|---|---|---|
| `DATABASE_URL` | `string` | **No** | `sqlite:///./inkloom_dev.db` | Connection string for database. For PostgreSQL, use `postgresql+psycopg://user:pass@host:5432/dbname`. For SQLite, use `sqlite:///./inkloom_dev.db`. |
| `GEMINI_API_KEY` | `string` | **No** | `None` | Google Gemini API key. If omitted, AI analysis is disabled (`ai_status="disabled"`), and the deterministic rule engine runs standalone. |
| `GEMINI_MODEL` | `string` | **No** | `gemini-3.8-flash` | Gemini model ID. Render production runs `gemini-3.6-flash`. Automatic fallback to `gemini-3.1-flash-lite` on quota/503. |
| `GEMINI_TIMEOUT_SECONDS` | `float` | **No** | `30.0` | Timeout in seconds for external Gemini API calls before triggering fallback or timing out. |
| `CORS_ORIGINS` | `string` | **No** | `http://localhost:5173,https://inkloom-ai-wheat.vercel.app` | Comma-separated list of allowed frontend origins for CORS headers. Regex `^https:\/\/.*\.vercel\.app$` is also permitted. |
| `JWT_SECRET_KEY` | `string` | **No** | (Pre-configured default) | Cryptographic secret key used to sign and verify session JWTs using HMAC-SHA256 (`HS256`). Must be $\ge 32$ characters in production. |
| `JWT_ALGORITHM` | `string` | **No** | `HS256` | JWT signing algorithm. Standard: `HS256`. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | **No** | `10080` (7 days) | Token expiration duration in minutes. |
| `DEMO_SEED_PASSWORD` | `string` | **No** | `""` (fallback in seed: `LumaCareDemo2026!`) | Password assigned to demo users during database seeding. |
| `MAX_CONTENT_CHARS` | `int` | **No** | `10000` | Maximum character length for a single content submission version. |
| `ANALYZE_RATE_LIMIT_PER_MINUTE` | `int` | **No** | `10` | Maximum compliance analysis requests per minute per client IP. |

### Frontend Environment Variables (`frontend/.env.local`)

| Variable | Type | Required? | Default / Fallback | Description & Safe Sample Value |
|---|---|---|---|---|
| `VITE_API_BASE_URL` | `string` | **No** | `""` (relative root) | Base URL for FastAPI backend. In local development: `http://localhost:8000`. In production: left empty or set to Render backend URL. |
| `VITE_DEMO_SEED_PASSWORD` | `string` | **No** | `""` | Optional helper for pre-filling demo login buttons during local testing. |

> [!SECURITY NOTE]  
> Never commit `.env` or `.env.local` files containing real production secrets. Both files are included in `.gitignore`.

---

## 6. Testing & Quality Assurance Guide

Inkloom AI enforces high software quality standards through automated contract testing, unit testing, security regression suites, and static analysis.

### Running Backend Pytest Suite (162 Tests)

Ensure your virtual environment is active in the `backend/` directory:

```bash
cd backend
source .venv/bin/activate

# Run all 162 automated tests with verbose output
pytest -v
```

All 162 tests pass in ~20 seconds:

```
======================= 162 passed, 1 warning in 20.85s ========================
```

#### Running Specific Test Suites

```bash
# Security & credential redaction tests (OAuth, API keys, private keys)
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
This test inspects `backend/app/schemas.py` and `frontend/src/types.ts` to assert that all enum values, interfaces, and field names match 100%.

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

The backend exposes **31 active REST endpoints** across authentication, brand management, document ingestion, content workflows, and system health:

### System & Health

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Root system health check (DB connectivity & AI readiness). |
| `GET` | `/api/health` | Public | Namespaced API health check. |

### Authentication & Organisation Team Management

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Register a new organisation and create its initial Brand Manager (`admin`). |
| `POST` | `/api/auth/login` | Public | Authenticate with email/password and receive signed JWT Bearer token. |
| `GET` | `/api/auth/me` | Authenticated | Retrieve current authenticated user profile, role, and organisation. |
| `GET` | `/api/auth/members` | Brand Manager (`admin`) | List all members belonging to the caller's organisation. |
| `POST` | `/api/auth/members` | Brand Manager (`admin`) | Add a new team member with assigned role (`admin`, `editor`, `reviewer`). |
| `GET` | `/api/auth/organisations/lookup` | Public | Search organisation names by prefix for guided login. |

### Brand Workspaces & Knowledge Management

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/brands` | Authenticated / Public | List accessible brand workspaces for caller's organisation. |
| `POST` | `/api/brands` | Brand Manager (`admin`) | Create a new brand workspace. |
| `GET` | `/api/brands/{identifier}` | Authenticated / Public | Retrieve complete brand knowledge (guidelines, facts, terms, assets) by ID or slug with tenant isolation. |
| `PATCH` | `/api/brands/{brand_id}` | Brand Manager (`admin`) | Update brand metadata (mission, tone, industry). |
| `POST` | `/api/brands/{brand_id}/guidelines` | Brand Manager (`admin`) | Add an active compliance guideline. |
| `DELETE` | `/api/brands/{brand_id}/guidelines/{code}` | Brand Manager (`admin`) | Deactivate a compliance guideline. |
| `POST` | `/api/brands/{brand_id}/facts` | Brand Manager (`admin`) | Add an approved factual statement. |
| `DELETE` | `/api/brands/{brand_id}/facts/{code}` | Brand Manager (`admin`) | Deactivate an approved fact. |
| `POST` | `/api/brands/{brand_id}/terms` | Brand Manager (`admin`) | Add a preferred or prohibited terminology rule. |
| `DELETE` | `/api/brands/{brand_id}/terms/{code}` | Brand Manager (`admin`) | Deactivate a terminology rule. |
| `GET` | `/api/brands/{brand_id}/assets` | Authenticated / Public | List visual brand assets (logos, palettes) for a brand. |
| `POST` | `/api/brands/{brand_id}/assets` | Brand Manager (`admin`) | Add a visual brand asset. |
| `DELETE` | `/api/brands/{brand_id}/assets/{asset_id}` | Brand Manager (`admin`) | Delete a visual brand asset. |

### Document Extraction & Visual Analysis

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/documents/extract` | Authenticated / Public | Ingest Word (`.docx`), PDF, scanned PDF (OCR), and images (`.png`, `.jpg`). Performs text extraction, OCR, and visual logo verification. |

### Content Submissions, Workflows & Reviews

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/submissions` | Authenticated / Public | List all submissions for the active brand workspace. |
| `POST` | `/api/submissions` | Authenticated / Public | Create a new submission draft and initial version `v1`. |
| `GET` | `/api/submissions/{id}` | Authenticated / Public | Retrieve full submission details, version history, and analysis runs. |
| `POST` | `/api/submissions/{id}/versions` | Authenticated / Public | Create a new immutable content version (`v2`, `v3`...). |
| `POST` | `/api/submissions/{id}/analyze` | Authenticated / Public | Run hybrid compliance analysis on current version. |
| `POST` | `/api/submissions/{id}/review-request` | Authenticated / Public | Submit an analyzed version for formal human review. |
| `POST` | `/api/submissions/{id}/reviews` | Auditor (`reviewer`) / Manager (`admin`) | Record authoritative human review decision (`approved`, `rejected`, `revisions_requested`). |
| `GET` | `/api/submissions/{id}/audit` | Authenticated / Public | Retrieve complete chronological audit trail. |
| `GET` | `/api/analysis-runs/{id}` | Authenticated / Public | Retrieve details of a specific historical analysis run. |

---

## 8. Demo Access & Evaluation Workflow

Inkloom AI includes pre-seeded demo accounts and one-click role switching on the live production web app:

### Option 1: Live Demo Role Launcher (Fastest Evaluation)
1. Visit the live login page at **[https://inkloom-ai-wheat.vercel.app/login](https://inkloom-ai-wheat.vercel.app/login)**.
2. Under **"Explore with live demo roles"**, click any of the 3 pre-configured role buttons:
   - **Brand Manager** (`admin@lumacare.demo`): Provision brands, configure guidelines, facts, terms, visual assets, and manage team members.
   - **Content Creator** (`editor@lumacare.demo`): Draft marketing copy, upload documents, trigger OCR, run compliance analysis, and request review.
   - **Compliance Auditor** (`reviewer@lumacare.demo`): Review submitted drafts, inspect claim grounding, and issue final review decisions.
3. The frontend authenticates through `POST /api/auth/login`, receives a signed JWT, selects the default LumaCare workspace, and routes to the workspace.

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

### 3. Gemini API 429 Quota or Unavailable (503)
- **Behavior**: Inkloom AI is designed with graceful resilience. If the primary Gemini model (`gemini-3.6-flash` / `gemini-3.8-flash`) returns a 503 error, the backend retries once, then automatically falls back to `gemini-3.1-flash-lite`. If no API key is provided or the quota is completely exhausted, the system marks `ai_status="disabled"` and completes the full analysis using the deterministic rule engine.

### 4. CORS Errors During Local Development
- **Cause**: Local frontend runs on a port not listed in `CORS_ORIGINS`.
- **Solution**: Add your frontend origin (e.g. `http://localhost:5173`) to `CORS_ORIGINS` in `backend/.env`.

### 5. Render Free-Tier Cold Start
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
