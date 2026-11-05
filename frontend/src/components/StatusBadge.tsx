/**
 * Clean status and severity badges.
 * Follows strict design system: warm earth tones (sage, terracotta, ochre),
 * subtle borders, no generic bright rainbow or neon.
 */

import type { FindingCategory, FindingType, OverallStatus, Severity, SubmissionStatus } from '../api/types'

interface OverallBadgeProps {
  status: OverallStatus | null
}

export function OverallBadge({ status }: OverallBadgeProps) {
  if (!status) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-parchment text-ink-soft rounded-sm border border-parchment-deep">
        Unanalyzed
      </span>
    )
  }

  switch (status) {
    case 'compliant':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider bg-sage-soft text-sage rounded-sm border border-sage/30">
          Compliant
        </span>
      )
    case 'needs_review':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider bg-ochre-soft text-ochre rounded-sm border border-ochre/30">
          Needs Review
        </span>
      )
    case 'non_compliant':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider bg-terracotta-soft text-terracotta rounded-sm border border-terracotta/30">
          Non-Compliant
        </span>
      )
  }
}

interface SubmissionStatusBadgeProps {
  status: SubmissionStatus
}

export function SubmissionStatusBadge({ status }: SubmissionStatusBadgeProps) {
  const labels: Record<SubmissionStatus, { text: string; style: string }> = {
    draft: { text: 'Draft', style: 'bg-parchment text-ink-soft border-parchment-deep' },
    analyzed: { text: 'Analyzed', style: 'bg-sage-soft text-sage border-sage/30' },
    in_review: { text: 'In Review', style: 'bg-ochre-soft text-ochre border-ochre/30' },
    approved: { text: 'Approved', style: 'bg-sage text-ivory border-sage' },
    rejected: { text: 'Rejected', style: 'bg-terracotta text-ivory border-terracotta' },
    revisions_requested: { text: 'Revisions Requested', style: 'bg-terracotta-soft text-terracotta border-terracotta/30' },
  }

  const { text, style } = labels[status] || { text: status, style: 'bg-parchment text-ink' }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-sm border ${style}`}>
      {text}
    </span>
  )
}

interface SeverityBadgeProps {
  severity: Severity
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const styles: Record<Severity, string> = {
    critical: 'bg-terracotta text-ivory border-terracotta',
    high: 'bg-terracotta-soft text-terracotta border-terracotta/30',
    medium: 'bg-ochre-soft text-ochre border-ochre/30',
    low: 'bg-parchment text-ink-soft border-parchment-deep',
    informational: 'bg-sage-soft text-sage border-sage/20',
  }

  const label = severity.charAt(0).toUpperCase() + severity.slice(1)

  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-sm border ${styles[severity]}`}>
      {label}
    </span>
  )
}

interface FindingTypeBadgeProps {
  type: FindingType
}

export function FindingTypeBadge({ type }: FindingTypeBadgeProps) {
  const labels: Record<FindingType, string> = {
    confirmed_rule_violation: 'Confirmed Violation',
    unsupported_claim: 'Unsupported Claim',
    potential_issue: 'Potential Issue',
    recommendation: 'Recommendation',
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 text-xs tracking-wide uppercase font-semibold text-ink-soft bg-parchment/60 rounded-sm border border-parchment-deep">
      {labels[type]}
    </span>
  )
}

interface CategoryBadgeProps {
  category: FindingCategory
}

export function CategoryBadge({ category }: CategoryBadgeProps) {
  const label = category.replace('_', ' ')
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-xs capitalize text-ink-soft bg-parchment rounded-sm border border-parchment-deep/60">
      {label}
    </span>
  )
}
