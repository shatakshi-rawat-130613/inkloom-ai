# API Contract (v2 — Round 3 Final)

Sources of truth: [`backend/app/schemas.py`](../backend/app/schemas.py), [`backend/app/enums.py`](../backend/app/enums.py), mirrored in [`frontend/src/api/types.ts`](../frontend/src/api/types.ts).  
All contract parity is verified by `backend/tests/test_contract_parity.py`.

- Base path: `/api`.
- JSON-first payloads; multipart form-data for `/api/documents/extract`.
- Authentication: Standard HTTP Bearer JWT tokens in `Authorization: Bearer <token>` header. Public demo endpoints remain accessible without auth.
- UUIDs as strings, datetimes in ISO 8601 UTC format.
- Multi-tenant isolation: Calling users can only view and modify resources within their registered organisation.

---

## 1. Enumerations

| Enum | Values |
|---|---|
| `UserRole` | `admin` (Brand Manager), `editor` (Content Creator), `reviewer` (Compliance Auditor) |
| `ContentType` | `social_post`, `email`, `web_page`, `advertisement`, `product_description`, `press_release`, `other` |
| `SubmissionStatus` | `draft`, `analyzed`, `in_review`, `approved`, `rejected`, `revisions_requested` |
| `OverallStatus` | `compliant`, `needs_review`, `non_compliant` |
| `FindingType` | `confirmed_rule_violation`, `unsupported_claim`, `potential_issue`, `recommendation` |
| `Severity` | `critical`, `high`, `medium`, `low`, `informational` |
| `FindingCategory` | `terminology`, `outcome_claim`, `factual_consistency`, `timeframe`, `tone`, `other` |
| `FindingSource` | `rule_engine`, `ai`, `visual` |
| `AIStatus` | `ok`, `unavailable`, `invalid_response`, `disabled` |
| `ReviewDecision` | `approved`, `rejected`, `revisions_requested` |
| `SubmissionAction` | `edit`, `analyze`, `request_review`, `review` |

---

## 2. API Endpoints Reference

### Authentication & Team Management (`/api/auth`)

- `POST /api/auth/register`: Create a new organisation and provision the first user as Brand Manager (`admin`).
- `POST /api/auth/login`: Authenticate with email/password and obtain a signed JWT Bearer token.
- `GET /api/auth/me`: Retrieve current session user profile, tenant organisation, and role.
- `GET /api/auth/members`: List team members in the user's organisation. Requires `admin` role.
- `POST /api/auth/members`: Invite/create a new team member with specified role (`admin`, `editor`, `reviewer`). Requires `admin` role.
- `PATCH /api/auth/members/{id}/role`: Modify a team member's role. Requires `admin` role.

### Multi-Brand Management (`/api/brands`)

- `GET /api/brands`: List all accessible brand workspaces (public demo + caller's organisation brands).
- `POST /api/brands`: Create a new brand workspace within the user's organisation. Requires `admin` role.
- `GET /api/brands/{slug_or_id}`: Retrieve detailed brand knowledge (guidelines, facts, terms, assets) with tenant isolation.
- `PATCH /api/brands/{id}`: Update brand workspace metadata (name, industry, voice, description). Requires `admin` role.
- `POST /api/brands/{id}/guidelines`: Add an active compliance guideline. Requires `admin` role.
- `DELETE /api/brands/{id}/guidelines/{code}`: Deactivate a compliance guideline. Requires `admin` role.
- `POST /api/brands/{id}/facts`: Add an approved factual statement. Requires `admin` role.
- `DELETE /api/brands/{id}/facts/{code}`: Deactivate an approved fact. Requires `admin` role.
- `POST /api/brands/{id}/terms`: Add a preferred or prohibited terminology rule. Requires `admin` role.
- `DELETE /api/brands/{id}/terms/{code}`: Deactivate a terminology rule. Requires `admin` role.
- `POST /api/brands/{id}/assets`: Upload/configure visual brand assets (logo specifications, color palettes). Requires `admin` role.
- `GET /api/brands/{id}/assets`: List visual brand assets for a brand.

### Multi-Format Document Ingestion & Vision (`/api/documents`)

- `POST /api/documents/extract`: Multipart upload accepting `.pdf`, `.docx`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg`, `.webp` (up to 10MB).
  - **Native & Scanned PDFs**: Parses text streams; automatically falls back to page image OCR if native text is absent.
  - **Word DOCX**: Extracts body text, paragraphs, headings, and table cells.
  - **Promotional Images**: Performs multimodal OCR, visual logo verification against approved references, dominant color palette extraction, and CIELAB color distance checks.

### Submissions & Governance Lifecycle (`/api/submissions`)

- `POST /api/submissions`: Create a new submission draft and initial immutable version (v1).
- `GET /api/submissions`: List submissions scoped to the caller's organisation or public demo.
- `GET /api/submissions/{id}`: Retrieve full submission detail, version history, analysis runs, and review audit trail.
- `POST /api/submissions/{id}/versions`: Create an immutable revision (v2, v3...), preserving all prior versions and audit records.
- `POST /api/submissions/{id}/analyze`: Run hybrid deterministic rule engine and Gemini evaluation against the current version.
- `POST /api/submissions/{id}/review-requests`: Submit an analyzed draft for human compliance review.
- `POST /api/submissions/{id}/reviews`: Record human reviewer decision (`approved`, `rejected`, `revisions_requested`) with required comments.
- `GET /api/submissions/{id}/audit`: Retrieve immutable chronological audit history.
