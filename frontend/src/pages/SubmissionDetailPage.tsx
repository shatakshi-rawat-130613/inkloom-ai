/**
 * Detailed Submission Governance & Review Workspace.
 *
 * Core capabilities:
 * - Version switcher with immutable historical preservation.
 * - Deterministic + AI compliance results inspection (findings, evidence, suggestions, positive observations).
 * - Inline revision drafting (creating version N+1 and re-analysing).
 * - Human review workflow (Approve, Reject, Request Revisions with mandatory comments).
 * - Audit trail logging.
 */

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type {
  AnalysisRun,
  AuditLogEntry,
  ReviewDecision,
  SubmissionDetail,
} from '../api/types'
import { Skeleton } from '../components/Skeleton'
import {
  CategoryBadge,
  FindingTypeBadge,
  OverallBadge,
  SeverityBadge,
  SubmissionStatusBadge,
} from '../components/StatusBadge'

export function SubmissionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null)
  const [selectedVersionNum, setSelectedVersionNum] = useState<number>(1)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Revision drafting mode state
  const [isDraftingRevision, setIsDraftingRevision] = useState(false)
  const [revisionBody, setRevisionBody] = useState('')
  const [revisionNote, setRevisionNote] = useState('')

  // Human Review Form state
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [reviewDecision, setReviewDecision] = useState<ReviewDecision>('approved')
  const [reviewerName, setReviewerName] = useState('Compliance Lead')
  const [reviewComments, setReviewComments] = useState('')

  // Audit trail state
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([])
  const [activeBottomTab, setActiveBottomTab] = useState<'findings' | 'history' | 'audit'>('findings')

  const [reloadTrigger, setReloadTrigger] = useState(0)

  // Selected historical analysis run (if user clicks an older run)
  const [activeAnalysisRun, setActiveAnalysisRun] = useState<AnalysisRun | null>(null)

  const reloadData = () => {
    setReloadTrigger((prev) => prev + 1)
  }

  useEffect(() => {
    let ignore = false

    async function fetchData() {
      if (!id) return
      try {
        const data = await api.getSubmission(id)
        if (ignore) return
        setSubmission(data)
        setSelectedVersionNum(data.current_version_number)
        setActiveAnalysisRun(data.latest_analysis)
        const audit = await api.getAuditTrail(id)
        if (ignore) return
        setAuditLog(audit)
        setLoading(false)
      } catch (err: unknown) {
        if (ignore) return
        setError(err instanceof Error ? err.message : 'Failed to load submission.')
        setLoading(false)
      }
    }

    void fetchData()

    return () => {
      ignore = true
    }
  }, [id, reloadTrigger])

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12 space-y-6">
        <Skeleton className="h-8 w-1/4" />
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    )
  }

  if (error || !submission) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-center">
        <h1 className="font-serif text-3xl text-terracotta">Submission Not Found</h1>
        <p className="mt-4 text-ink-soft">{error || 'Could not retrieve content submission details.'}</p>
        <Link
          to="/"
          className="mt-6 inline-block px-4 py-2 bg-parchment text-ink text-sm font-medium rounded-sm border border-parchment-deep"
        >
          Return to Workspace
        </Link>
      </div>
    )
  }

  // Find currently selected version
  const selectedVersion =
    submission.versions.find((v) => v.version_number === selectedVersionNum) ||
    submission.versions[submission.versions.length - 1]

  // Handlers
  const handleStartRevision = () => {
    setRevisionBody(selectedVersion.body)
    setRevisionNote(`Revision based on version ${selectedVersion.version_number}`)
    setIsDraftingRevision(true)
  }

  const handleSaveAndAnalyzeRevision = async () => {
    if (!revisionBody.trim()) return
    setActionLoading(true)
    setError(null)
    try {
      await api.createVersion(submission.id, {
        body: revisionBody.trim(),
        change_note: revisionNote.trim() || undefined,
      })
      await api.analyzeSubmission(submission.id)
      setIsDraftingRevision(false)
      await reloadData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save and re-analyse revision.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReanalyzeCurrent = async () => {
    setActionLoading(true)
    setError(null)
    try {
      await api.analyzeSubmission(submission.id)
      await reloadData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRequestReview = async () => {
    setActionLoading(true)
    setError(null)
    try {
      await api.requestReview(submission.id, {
        requested_by: submission.author_name,
        note: 'Submitted for formal brand governance sign-off.',
      })
      await reloadData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to request review.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleRecordReview = async (e: React.FormEvent) => {
    e.preventDefault()
    if (reviewDecision !== 'approved' && !reviewComments.trim()) {
      setError('Comments are required when requesting revisions or rejecting content.')
      return
    }

    setActionLoading(true)
    setError(null)
    try {
      await api.recordReview(submission.id, {
        decision: reviewDecision,
        reviewer_name: reviewerName.trim() || 'Compliance Lead',
        comments: reviewComments.trim() || null,
      })
      setShowReviewModal(false)
      await reloadData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to submit review decision.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSelectHistoricalRun = async (runId: string) => {
    setActionLoading(true)
    try {
      const run = await api.getAnalysisRun(runId)
      setActiveAnalysisRun(run)
      setSelectedVersionNum(run.version_number)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis run.')
    } finally {
      setActionLoading(false)
    }
  }

  const findings = activeAnalysisRun?.findings || []
  const positiveObservations = activeAnalysisRun?.positive_observations || []
  const isUnrelatedToBrand =
    Boolean(activeAnalysisRun?.summary?.startsWith('UNRELATED TO ACTIVE BRAND')) ||
    findings.some((f) => f.reference_note?.includes('UNRELATED_TO_BRAND'))

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 space-y-8">
      {/* Top Breadcrumb & Metadata Header */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2 text-xs text-ink-soft">
          <Link to="/" className="hover:text-ink transition-colors">
            {submission.brand_name} Workspace
          </Link>
          <span>/</span>
          <span className="text-ink font-medium">Submissions</span>
          <span>/</span>
          <span className="font-mono text-sage">{submission.id.slice(0, 8)}</span>
        </div>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-parchment-deep pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="font-serif text-3xl font-bold text-ink">{submission.title}</h1>
              <SubmissionStatusBadge status={submission.status} />
              <OverallBadge status={submission.latest_overall_status} />
            </div>
            <p className="text-xs text-ink-soft">
              Author: <span className="font-semibold text-ink">{submission.author_name}</span> | Type:{' '}
              <span className="capitalize">{submission.content_type.replace('_', ' ')}</span> | Current
              Version: <span className="font-mono font-bold">v{submission.current_version_number}</span>
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2">
            {submission.allowed_actions.includes('edit') && !isDraftingRevision && (
              <button
                onClick={handleStartRevision}
                className="px-3.5 py-1.5 text-xs font-medium text-ink bg-parchment border border-parchment-deep rounded-sm hover:bg-parchment-deep transition-colors"
              >
                Create Revision
              </button>
            )}

            {submission.allowed_actions.includes('analyze') && !isDraftingRevision && (
              <button
                onClick={handleReanalyzeCurrent}
                disabled={actionLoading}
                className="px-3.5 py-1.5 text-xs font-medium text-ink bg-parchment border border-parchment-deep rounded-sm hover:bg-parchment-deep disabled:opacity-50 transition-colors"
              >
                {actionLoading ? 'Analysing...' : 'Re-analyse'}
              </button>
            )}

            {submission.allowed_actions.includes('request_review') && !isDraftingRevision && (
              <button
                onClick={handleRequestReview}
                disabled={actionLoading}
                className="px-4 py-1.5 text-xs font-semibold text-ivory bg-sage hover:bg-sage/90 rounded-sm transition-colors"
              >
                Submit for Human Review
              </button>
            )}

            {submission.allowed_actions.includes('review') && (
              <button
                onClick={() => setShowReviewModal(true)}
                className="px-4 py-1.5 text-xs font-semibold text-ivory bg-ink hover:bg-ink-soft rounded-sm transition-colors"
              >
                Record Review Decision
              </button>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-terracotta-soft/30 border border-terracotta/40 rounded-sm text-xs text-terracotta">
          {error}
        </div>
      )}

      {/* Main Two-Column Workflow Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Content Version Inspector / Revision Editor (7 cols) */}
        <div className="lg:col-span-7 bg-ivory border border-parchment-deep rounded-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-parchment-deep/60 pb-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs uppercase tracking-wider font-semibold text-ink-soft">
                Version History:
              </span>
              <div className="flex items-center space-x-1">
                {submission.versions.map((ver) => (
                  <button
                    key={ver.id}
                    onClick={() => {
                      setSelectedVersionNum(ver.version_number)
                      setIsDraftingRevision(false)
                    }}
                    className={`px-2.5 py-1 text-xs font-mono rounded-sm transition-colors ${
                      selectedVersionNum === ver.version_number && !isDraftingRevision
                        ? 'bg-ink text-ivory font-bold'
                        : 'bg-parchment text-ink-soft hover:text-ink'
                    }`}
                  >
                    v{ver.version_number}
                  </button>
                ))}
              </div>
            </div>

            {selectedVersion.change_note && (
              <span className="text-xs text-ink-soft italic truncate max-w-xs">
                "{selectedVersion.change_note}"
              </span>
            )}
          </div>

          {/* Body Viewer or Revision Editor */}
          {isDraftingRevision ? (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-sage uppercase tracking-wider">
                  Drafting Revision v{submission.current_version_number + 1}
                </span>
                <span className="text-xs text-ink-soft font-mono">
                  {revisionBody.length} / 10,000 chars
                </span>
              </div>

              <textarea
                rows={10}
                value={revisionBody}
                onChange={(e) => setRevisionBody(e.target.value)}
                className="w-full p-4 text-sm font-sans leading-relaxed bg-ivory border border-sage rounded-sm text-ink focus:outline-none"
                placeholder="Make edits to align with approved guidelines and terminology..."
              />

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Change Note
                </label>
                <input
                  type="text"
                  value={revisionNote}
                  onChange={(e) => setRevisionNote(e.target.value)}
                  placeholder="e.g. Replaced guarantee with approved clearer-skin claim"
                  className="w-full px-3 py-2 text-xs bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-parchment-deep/60">
                <button
                  type="button"
                  onClick={() => setIsDraftingRevision(false)}
                  className="px-3 py-1.5 text-xs text-ink-soft hover:text-ink transition-colors"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={handleSaveAndAnalyzeRevision}
                  disabled={actionLoading || !revisionBody.trim()}
                  className="px-5 py-2 text-xs font-semibold bg-ink text-ivory rounded-sm hover:bg-ink-soft disabled:opacity-50 transition-colors"
                >
                  {actionLoading ? 'Saving and Analysing...' : 'Save and Re-analyse'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-5 bg-parchment/30 border border-parchment-deep/60 rounded-sm font-sans text-sm text-ink leading-relaxed whitespace-pre-wrap">
                {selectedVersion.body}
              </div>

              <div className="text-xs text-ink-soft flex items-center justify-between pt-2">
                <span>
                  Saved {new Date(selectedVersion.created_at).toLocaleString()}
                </span>
                <span>{selectedVersion.body.split(/\s+/).filter(Boolean).length} words</span>
              </div>
            </div>
          )}

          {/* Historical Reviews attached to this submission */}
          {submission.reviews.length > 0 && (
            <div className="mt-6 pt-6 border-t border-parchment-deep space-y-3">
              <h3 className="font-serif text-sm font-semibold text-ink">Recorded Human Reviews</h3>
              <div className="space-y-2">
                {submission.reviews.map((rev) => (
                  <div
                    key={rev.id}
                    className="p-3 bg-parchment/40 border border-parchment-deep rounded-sm space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-ink">
                        {rev.reviewer_name} (on v{rev.version_number})
                      </span>
                      <SubmissionStatusBadge
                        status={
                          rev.decision === 'approved'
                            ? 'approved'
                            : rev.decision === 'rejected'
                              ? 'rejected'
                              : 'revisions_requested'
                        }
                      />
                    </div>
                    {rev.comments && <p className="text-ink-soft italic pt-1">"{rev.comments}"</p>}
                    <p className="text-[10px] text-ink-soft pt-1">
                      {new Date(rev.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Governance Findings & Analysis Engine Output (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {activeAnalysisRun ? (
            <div className="bg-ivory border border-parchment-deep rounded-sm p-6 space-y-6">
              {/* Overall Status Banner */}
              <div className="space-y-2">
                {isUnrelatedToBrand && (
                  <div className="flex items-center justify-between pb-1">
                    <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
                      Brand Relevance
                    </span>
                    <span className="px-2 py-0.5 rounded-sm font-mono text-[11px] font-bold uppercase tracking-wider bg-terracotta/15 text-terracotta border border-terracotta/30">
                      UNRELATED TO ACTIVE BRAND
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
                    Compliance Status
                  </span>
                  <OverallBadge status={activeAnalysisRun.overall_status} />
                </div>

                {isUnrelatedToBrand && (
                  <div className="p-4 bg-terracotta/10 border border-terracotta/30 rounded-sm space-y-2 my-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs uppercase tracking-wider font-semibold text-terracotta">
                        Brand Relevance Assessment
                      </span>
                      <span className="text-[11px] font-medium text-ochre bg-ochre-soft/40 px-2 py-0.5 rounded-sm border border-ochre/30">
                        Active Brand: {submission.brand_name || 'LumaCare'}
                      </span>
                    </div>
                    <p className="text-xs text-ink leading-relaxed">
                      The submitted content appears to describe a brand, product category or industry that is unrelated to {submission.brand_name || 'LumaCare'}, the currently active skincare brand. Its compliance cannot be reliably assessed against {submission.brand_name || 'LumaCare'}'s approved guidelines and product information.
                    </p>
                    <div className="text-xs text-ink-soft pt-1">
                      <span className="font-semibold text-ink">Recommendation: </span>
                      Submit content relevant to {submission.brand_name || 'LumaCare'} or provide additional context to clarify its relationship with the active brand.
                    </div>
                  </div>
                )}

                <p className="text-xs text-ink-soft leading-relaxed">
                  {activeAnalysisRun.summary}
                </p>

                <div className="flex items-center gap-3 pt-2 text-[11px] text-ink-soft border-t border-parchment-deep/40">
                  <span>Engine v{activeAnalysisRun.rule_engine_version}</span>
                  <span>|</span>
                  <span>AI: {activeAnalysisRun.ai_status}</span>
                  <span>|</span>
                  <span>Duration: {activeAnalysisRun.duration_ms}ms</span>
                </div>
              </div>

              {/* Positive Observations */}
              {positiveObservations.length > 0 && (
                <div className="p-4 bg-sage-soft/30 border border-sage/30 rounded-sm space-y-2">
                  <span className="text-xs uppercase tracking-wider font-semibold text-sage">
                    Positive Brand Observations
                  </span>
                  <ul className="space-y-1 text-xs text-ink">
                    {positiveObservations.map((obs, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-sage font-bold">&bull;</span>
                        <span>{obs}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Finding Summary Count */}
              <div className="flex items-center justify-between border-b border-parchment-deep/60 pb-2">
                <h3 className="font-serif text-base font-semibold text-ink">
                  Detailed Findings ({findings.length})
                </h3>
                {activeAnalysisRun.requires_human_review && (
                  <span className="text-[11px] font-medium text-ochre bg-ochre-soft/40 px-2 py-0.5 rounded-sm border border-ochre/30">
                    Human Review Required
                  </span>
                )}
              </div>

              {/* Findings Cards List */}
              {findings.length === 0 ? (
                <div className="text-center py-8 text-xs text-ink-soft">
                  {isUnrelatedToBrand ? (
                    <>
                      <p className="font-serif text-sm font-semibold text-ochre">Unrelated Content</p>
                      <p className="mt-1">Content does not relate to active brand; no brand-specific violations applied.</p>
                    </>
                  ) : (
                    <>
                      <p className="font-serif text-sm font-semibold text-sage">No violations detected</p>
                      <p className="mt-1">Content meets approved brand guidelines and factual standards.</p>
                    </>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {findings.map((finding) => (
                    <div
                      key={finding.id}
                      className="p-4 bg-parchment/20 border border-parchment-deep rounded-sm space-y-3 text-xs"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-1.5">
                          <SeverityBadge severity={finding.severity} />
                          <FindingTypeBadge type={finding.finding_type} />
                        </div>
                        <CategoryBadge category={finding.category} />
                      </div>

                      {/* Quoted Text */}
                      <div className="p-2.5 bg-ivory border border-parchment-deep/60 rounded-sm space-y-1">
                        <span className="text-[10px] uppercase font-semibold text-ink-soft">
                          Original Text:
                        </span>
                        <p className="font-mono text-xs text-terracotta font-medium">
                          "{finding.original_text}"
                        </p>
                      </div>

                      {/* Cited Rule and Evidence */}
                      {(finding.guideline_id || finding.approved_fact_id || finding.approved_term_id) && (
                        <div className="space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-ink-soft">
                            Approved Standard Reference:
                          </span>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {finding.guideline_id && (
                              <span className="font-mono font-bold text-[11px] text-sage px-1.5 py-0.5 bg-sage-soft/40 rounded-sm border border-sage/20">
                                {finding.guideline_id}
                              </span>
                            )}
                            {finding.approved_fact_id && (
                              <span className="font-mono font-bold text-[11px] text-sage px-1.5 py-0.5 bg-sage-soft/40 rounded-sm border border-sage/20">
                                {finding.approved_fact_id}
                              </span>
                            )}
                            {finding.approved_term_id && (
                              <span className="font-mono font-bold text-[11px] text-sage px-1.5 py-0.5 bg-sage-soft/40 rounded-sm border border-sage/20">
                                {finding.approved_term_id}
                              </span>
                            )}
                          </div>
                          {finding.evidence && (
                            <p className="text-[11px] text-ink-soft italic pt-1">
                              Evidence: "{finding.evidence}"
                            </p>
                          )}
                        </div>
                      )}

                      {/* Explanation */}
                      <div className="space-y-1">
                        <span className="text-[10px] uppercase font-semibold text-ink-soft">
                          Reasoning:
                        </span>
                        <p className="text-ink leading-relaxed">{finding.explanation}</p>
                      </div>

                      {/* Actionable Suggestion */}
                      {finding.suggestion && (
                        <div className="p-2.5 bg-sage-soft/20 border border-sage/20 rounded-sm space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-sage">
                            Recommended Correction:
                          </span>
                          <p className="text-xs text-ink">{finding.suggestion}</p>
                        </div>
                      )}

                      {/* Reference Note if corrected by validator */}
                      {finding.reference_note && (
                        <p className="text-[10px] text-ochre bg-ochre-soft/30 p-2 rounded-sm border border-ochre/20">
                          {finding.reference_note}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-ivory border border-parchment-deep rounded-sm p-8 text-center space-y-4">
              <p className="font-serif text-base text-ink">No analysis available for this version</p>
              <button
                onClick={handleReanalyzeCurrent}
                disabled={actionLoading}
                className="px-4 py-2 bg-ink text-ivory text-xs font-semibold rounded-sm hover:bg-ink-soft transition-colors"
              >
                Run Analysis Now
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Tabs: Historical Runs & Audit Trail */}
      <div className="bg-ivory border border-parchment-deep rounded-sm p-6 space-y-4">
        <div className="flex items-center space-x-4 border-b border-parchment-deep pb-3">
          <button
            onClick={() => setActiveBottomTab('findings')}
            className={`text-xs font-semibold uppercase tracking-wider pb-1 transition-colors ${
              activeBottomTab === 'findings'
                ? 'text-ink border-b-2 border-ink'
                : 'text-ink-soft hover:text-ink'
            }`}
          >
            Analysis Runs History ({submission.analysis_runs.length})
          </button>
          <button
            onClick={() => setActiveBottomTab('audit')}
            className={`text-xs font-semibold uppercase tracking-wider pb-1 transition-colors ${
              activeBottomTab === 'audit'
                ? 'text-ink border-b-2 border-ink'
                : 'text-ink-soft hover:text-ink'
            }`}
          >
            Immutable Audit Trail ({auditLog.length})
          </button>
        </div>

        {activeBottomTab === 'findings' && (
          <div className="space-y-2">
            {submission.analysis_runs.map((run, i) => (
              <div
                key={run.id}
                onClick={() => handleSelectHistoricalRun(run.id)}
                className={`flex items-center justify-between p-3 rounded-sm border cursor-pointer transition-colors text-xs ${
                  activeAnalysisRun?.id === run.id
                    ? 'bg-parchment border-sage'
                    : 'bg-ivory border-parchment-deep hover:bg-parchment/40'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="font-mono font-bold text-ink">Run #{i + 1}</span>
                  <span className="font-mono text-ink-soft">on v{run.version_number}</span>
                  <OverallBadge status={run.overall_status} />
                  <span className="text-ink-soft">({run.finding_count} findings)</span>
                </div>

                <div className="flex items-center space-x-4 text-ink-soft">
                  <span>{new Date(run.created_at).toLocaleTimeString()}</span>
                  <span className="text-sage font-medium">View &rarr;</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeBottomTab === 'audit' && (
          <div className="divide-y divide-parchment-deep/60">
            {auditLog.map((entry) => (
              <div key={entry.id} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3">
                  <span className="font-mono font-medium text-sage uppercase">{entry.action}</span>
                  <span className="text-ink font-medium">by {entry.actor_name}</span>
                </div>
                <span className="text-ink-soft font-mono">
                  {new Date(entry.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Human Review Modal Dialog */}
      {showReviewModal && (
        <div className="fixed inset-0 z-50 bg-ink/50 flex items-center justify-center p-4">
          <div className="bg-ivory border border-parchment-deep p-6 rounded-sm max-w-lg w-full space-y-6">
            <div>
              <h2 className="font-serif text-xl font-bold text-ink">Record Human Review Decision</h2>
              <p className="text-xs text-ink-soft mt-1">
                As a designated brand reviewer, confirm approval, request modifications, or reject.
              </p>
            </div>

            <form onSubmit={handleRecordReview} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Decision
                </label>
                <select
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value as ReviewDecision)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
                >
                  <option value="approved">Approve Content</option>
                  <option value="revisions_requested">Request Revisions</option>
                  <option value="rejected">Reject Content</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Reviewer Name
                </label>
                <input
                  type="text"
                  required
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Review Comments {reviewDecision !== 'approved' && '(Required)'}
                </label>
                <textarea
                  rows={4}
                  required={reviewDecision !== 'approved'}
                  value={reviewComments}
                  onChange={(e) => setReviewComments(e.target.value)}
                  placeholder="Provide clear rationale, required modifications, or sign-off notes..."
                  className="w-full p-3 text-xs bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-parchment-deep/60">
                <button
                  type="button"
                  onClick={() => setShowReviewModal(false)}
                  className="px-4 py-2 text-xs font-medium text-ink-soft hover:text-ink transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2 text-xs font-semibold bg-ink text-ivory rounded-sm hover:bg-ink-soft disabled:opacity-50 transition-colors"
                >
                  {actionLoading ? 'Recording...' : 'Commit Review Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
