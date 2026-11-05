/**
 * Typed API client for Inkloom AI.
 * Handles base URL configuration, typed requests, and ErrorResponse unwrapping.
 */

import type {
  AnalysisRun,
  AuditLogEntry,
  BrandDetail,
  BrandSummary,
  ErrorResponse,
  HealthResponse,
  ReviewCreate,
  ReviewRequestCreate,
  SubmissionCreate,
  SubmissionDetail,
  SubmissionListItem,
  SubmissionStatus,
  UUID,
  VersionCreate,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

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
  getHealth: () => request<HealthResponse>('/api/health'),

  listBrands: () => request<BrandSummary[]>('/api/brands'),

  getBrand: (slug: string) => request<BrandDetail>(`/api/brands/${slug}`),

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
