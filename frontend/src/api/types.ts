/**
 * Inkloom AI API contract types.
 *
 * Centrally controlled. Mirrors backend/app/enums.py and backend/app/schemas.py
 * field for field. backend/tests/test_contract_parity.py fails if they drift.
 *
 * Conventions
 * - UUIDs and datetimes are strings (ISO 8601, UTC).
 * - Brand knowledge items use stable codes as `id` (GUIDE-001, FACT-001, TERM-001).
 *   Finding.guideline_id / approved_fact_id / approved_term_id hold those codes.
 * - Nullable backend fields are typed `T | null` (never omitted).
 */

export type UUID = string
export type ISODateTime = string

// ---------------------------------------------------------------- enums

export type ContentType =
  | 'social_post'
  | 'email'
  | 'web_page'
  | 'advertisement'
  | 'product_description'
  | 'press_release'
  | 'other'

export type SubmissionStatus =
  | 'draft'
  | 'analyzed'
  | 'in_review'
  | 'approved'
  | 'rejected'
  | 'revisions_requested'

export type OverallStatus = 'compliant' | 'needs_review' | 'non_compliant'

export type FindingType =
  | 'confirmed_rule_violation'
  | 'unsupported_claim'
  | 'potential_issue'
  | 'recommendation'

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'informational'

export type FindingCategory =
  | 'terminology'
  | 'outcome_claim'
  | 'factual_consistency'
  | 'timeframe'
  | 'tone'
  | 'other'

export type FindingSource = 'rule_engine' | 'ai' | 'document' | 'ocr' | 'visual'

export type AIStatus = 'ok' | 'unavailable' | 'invalid_response' | 'disabled'

export type ReviewDecision = 'approved' | 'rejected' | 'revisions_requested'

export type SubmissionAction = 'edit' | 'analyze' | 'request_review' | 'review'

export type UserRole = 'admin' | 'editor' | 'reviewer'

// ---------------------------------------------------------------- errors

export interface ErrorBody {
  code: string
  message: string
  details: Record<string, unknown>[] | null
}

export interface ErrorResponse {
  error: ErrorBody
}

// ---------------------------------------------------------------- brand knowledge

export interface Guideline {
  id: string
  title: string
  text: string
  category: FindingCategory
  default_severity: Severity
}

export interface Fact {
  id: string
  statement: string
  source: string | null
}

export interface Term {
  id: string
  preferred_term: string | null
  prohibited_term: string | null
  notes: string | null
  related_guideline_id: string | null
}

export interface BrandSummary {
  id: UUID
  slug: string
  name: string
  industry: string
  description: string
  is_demo: boolean
  organisation_id: UUID | null
}

export interface BrandDetail extends BrandSummary {
  voice_summary: string
  guidelines: Guideline[]
  facts: Fact[]
  terms: Term[]
}

// ---------------------------------------------------------------- findings and runs

export interface Finding {
  id: UUID
  position: number
  source: FindingSource
  category: FindingCategory
  severity: Severity
  finding_type: FindingType
  original_text: string
  start_offset: number | null
  end_offset: number | null
  guideline_id: string | null
  approved_fact_id: string | null
  approved_term_id: string | null
  evidence: string | null
  explanation: string
  suggestion: string | null
  confidence: number
  reference_note: string | null
}

export interface SeverityCounts {
  critical: number
  high: number
  medium: number
  low: number
  informational: number
}

export interface AnalysisRunSummary {
  id: UUID
  version_id: UUID
  version_number: number
  overall_status: OverallStatus
  requires_human_review: boolean
  ai_status: AIStatus
  finding_count: number
  severity_counts: SeverityCounts
  created_at: ISODateTime
}

export interface AnalysisRun extends AnalysisRunSummary {
  submission_id: UUID
  summary: string
  positive_observations: string[]
  model_name: string | null
  rule_engine_version: string
  duration_ms: number | null
  findings: Finding[]
}

// ---------------------------------------------------------------- submissions

export interface ContentVersion {
  id: UUID
  version_number: number
  body: string
  change_note: string | null
  created_at: ISODateTime
  analysis_run_ids: UUID[]
}

export interface HumanReview {
  id: UUID
  version_id: UUID
  version_number: number
  analysis_run_id: UUID | null
  reviewer_name: string
  decision: ReviewDecision
  comments: string | null
  created_at: ISODateTime
}

export interface AuditLogEntry {
  id: UUID
  entity_type: string
  entity_id: UUID
  action: string
  actor_name: string
  details: Record<string, unknown>
  created_at: ISODateTime
}

export interface SubmissionListItem {
  id: UUID
  brand_id: UUID
  brand_name: string
  title: string
  content_type: ContentType
  status: SubmissionStatus
  current_version_number: number
  latest_overall_status: OverallStatus | null
  author_name: string
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface SubmissionDetail extends SubmissionListItem {
  versions: ContentVersion[]
  analysis_runs: AnalysisRunSummary[]
  latest_analysis: AnalysisRun | null
  reviews: HumanReview[]
  allowed_actions: SubmissionAction[]
}

// ---------------------------------------------------------------- requests

export interface SubmissionCreate {
  brand_id: UUID
  title: string
  content_type: ContentType
  body: string
  author_name?: string
}

export interface VersionCreate {
  body: string
  change_note?: string | null
}

export interface ReviewRequestCreate {
  requested_by?: string
  note?: string | null
}

export interface ReviewCreate {
  decision: ReviewDecision
  reviewer_name: string
  comments?: string | null
}

export interface HealthResponse {
  status: string
  database: string
  ai: AIStatus
}

export interface UserResponse {
  id: UUID
  organisation_id: UUID
  organisation_name: string
  display_name: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: ISODateTime
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export interface OrganisationLookupResponse {
  exists: boolean
  name: string | null
  slug: string | null
  message: string | null
}

export interface UserRegisterRequest {
  organisation_name: string
  display_name: string
  email: string
  password: string
}

export interface UserLoginRequest {
  email: string
  password: string
}

export interface MemberCreateRequest {
  display_name: string
  email: string
  password: string
  role: UserRole
}

export interface BrandCreateRequest {
  name: string
  industry: string
  description: string
  voice_summary: string
}

export interface BrandUpdateRequest {
  name?: string | null
  industry?: string | null
  description?: string | null
  voice_summary?: string | null
}

export interface GuidelineCreateRequest {
  code: string
  title: string
  rule_text: string
  category: FindingCategory
  default_severity: Severity
}

export interface FactCreateRequest {
  code: string
  statement: string
  source?: string | null
}

export interface TermCreateRequest {
  code: string
  preferred_term?: string | null
  prohibited_term?: string | null
  notes?: string | null
  related_guideline_code?: string | null
}

export interface BrandAssetCreateRequest {
  asset_type: string
  name: string
  asset_metadata: Record<string, unknown>
}

export interface BrandAssetResponse {
  id: UUID
  brand_id: UUID
  asset_type: string
  name: string
  asset_metadata: Record<string, unknown>
  is_active: boolean
  created_at: ISODateTime
}

export interface DocumentExtractionResponse {
  id: UUID
  submission_id: UUID | null
  file_name: string
  file_type: string
  file_size_bytes: number
  extraction_source: string
  extracted_text: string
  extraction_status: string
  extraction_metadata: Record<string, unknown>
  created_at: ISODateTime
}

export interface DocumentExtractResponse {
  file_name: string
  file_type: string
  file_size_bytes: number
  extraction_source: string
  extracted_text: string
  extraction_metadata: Record<string, unknown>
  visual_findings: Record<string, unknown>[]
}

export const MAX_BODY_CHARS = 10_000
