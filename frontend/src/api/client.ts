/**
 * Typed API client for Inkloom AI.
 * Handles base URL configuration, Bearer auth headers, typed requests, and ErrorResponse unwrapping.
 */

import type {
  AnalysisRun,
  AuditLogEntry,
  AuthResponse,
  BrandAssetCreateRequest,
  BrandAssetResponse,
  BrandCreateRequest,
  BrandDetail,
  BrandSummary,
  BrandUpdateRequest,
  DocumentExtractResponse,
  ErrorResponse,
  FactCreateRequest,
  GuidelineCreateRequest,
  HealthResponse,
  MemberCreateRequest,
  ReviewCreate,
  ReviewRequestCreate,
  SubmissionCreate,
  SubmissionDetail,
  SubmissionListItem,
  SubmissionStatus,
  TermCreateRequest,
  UUID,
  UserLoginRequest,
  UserRegisterRequest,
  UserResponse,
  VersionCreate,
} from './types'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

export class ApiError extends Error {
  code: string
  details: Record<string, unknown>[] | null

  constructor(code: string, message: string, details: Record<string, unknown>[] | null = null) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  // Attach JWT Bearer token from localStorage if available
  const token = typeof window !== 'undefined' ? localStorage.getItem('inkloom_token') : null
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    let errorCode = 'http_error'
    let errorMessage = `Request failed with status ${response.status}`
    let errorDetails = null

    try {
      const errorJson = (await response.json()) as ErrorResponse
      if (errorJson.error) {
        errorCode = errorJson.error.code
        errorMessage = errorJson.error.message
        errorDetails = errorJson.error.details
      }
    } catch {
      // response was not json
    }

    throw new ApiError(errorCode, errorMessage, errorDetails)
  }

  return (await response.json()) as T
}

export const api = {
  // Health
  getHealth: () => request<HealthResponse>('/api/health'),

  // Auth & Organisation
  register: (payload: UserRegisterRequest) =>
    request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: UserLoginRequest) =>
    request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMe: () => request<UserResponse>('/api/auth/me'),

  listMembers: () => request<UserResponse[]>('/api/auth/members'),

  createMember: (payload: MemberCreateRequest) =>
    request<UserResponse>('/api/auth/members', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Brands
  listBrands: () => request<BrandSummary[]>('/api/brands'),

  getBrand: (slugOrId: string) => request<BrandDetail>(`/api/brands/${slugOrId}`),

  createBrand: (payload: BrandCreateRequest) =>
    request<BrandDetail>('/api/brands', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateBrand: (brandId: UUID, payload: BrandUpdateRequest) =>
    request<BrandDetail>(`/api/brands/${brandId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  addGuideline: (brandId: UUID, payload: GuidelineCreateRequest) =>
    request<BrandDetail>(`/api/brands/${brandId}/guidelines`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  addFact: (brandId: UUID, payload: FactCreateRequest) =>
    request<BrandDetail>(`/api/brands/${brandId}/facts`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  addTerm: (brandId: UUID, payload: TermCreateRequest) =>
    request<BrandDetail>(`/api/brands/${brandId}/terms`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listBrandAssets: (brandId: UUID) =>
    request<BrandAssetResponse[]>(`/api/brands/${brandId}/assets`),

  createBrandAsset: (brandId: UUID, payload: BrandAssetCreateRequest) =>
    request<BrandAssetResponse>(`/api/brands/${brandId}/assets`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Documents & Visual Ingestion
  extractDocument: async (file: File, brandId?: UUID) => {
    const formData = new FormData()
    formData.append('file', file)
    if (brandId) formData.append('brand_id', brandId)

    const token = typeof window !== 'undefined' ? localStorage.getItem('inkloom_token') : null
    const headers: Record<string, string> = {
      Accept: 'application/json',
    }
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}/api/documents/extract`, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (!res.ok) {
      let msg = `Document extraction failed with status ${res.status}`
      try {
        const errJson = await res.json()
        if (errJson.detail) msg = errJson.detail
      } catch {
        // ignore
      }
      throw new Error(msg)
    }

    return (await res.json()) as DocumentExtractResponse
  },

  // Submissions
  createSubmission: (payload: SubmissionCreate) =>
    request<SubmissionDetail>('/api/submissions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listSubmissions: (brandId?: UUID, status?: SubmissionStatus) => {
    const params = new URLSearchParams()
    if (brandId) params.set('brand_id', brandId)
    if (status) params.set('status', status)
    const qs = params.toString() ? `?${params.toString()}` : ''
    return request<SubmissionListItem[]>(`/api/submissions${qs}`)
  },

  getSubmission: (id: UUID) => request<SubmissionDetail>(`/api/submissions/${id}`),

  createVersion: (submissionId: UUID, payload: VersionCreate) =>
    request<SubmissionDetail>(`/api/submissions/${submissionId}/versions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  analyzeSubmission: (submissionId: UUID) =>
    request<AnalysisRun>(`/api/submissions/${submissionId}/analyze`, {
      method: 'POST',
    }),

  getAnalysisRun: (runId: UUID) => request<AnalysisRun>(`/api/analysis-runs/${runId}`),

  requestReview: (submissionId: UUID, payload: ReviewRequestCreate = {}) =>
    request<SubmissionDetail>(`/api/submissions/${submissionId}/review-request`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  recordReview: (submissionId: UUID, payload: ReviewCreate) =>
    request<SubmissionDetail>(`/api/submissions/${submissionId}/reviews`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getAuditTrail: (submissionId: UUID) =>
    request<AuditLogEntry[]>(`/api/submissions/${submissionId}/audit`),
}
