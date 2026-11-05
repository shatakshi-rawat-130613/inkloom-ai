/**
 * LumaCare Demo Brand Workspace page.
 * Displays approved guidelines, facts, terminology, and submission history.
 */

import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { BrandDetail, SubmissionListItem } from '../api/types'
import { Skeleton } from '../components/Skeleton'
import { CategoryBadge, OverallBadge, SeverityBadge, SubmissionStatusBadge } from '../components/StatusBadge'
import { DEMO_TEST_CASES } from '../data/demoTestCases'

export function WorkspacePage() {
  const navigate = useNavigate()
  const [brand, setBrand] = useState<BrandDetail | null>(null)
  const [submissions, setSubmissions] = useState<SubmissionListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'guidelines' | 'facts' | 'terms'>('guidelines')

  useEffect(() => {
    let mounted = true
    Promise.all([api.getBrand('lumacare'), api.listSubmissions()])
      .then(([brandData, subsData]) => {
        if (mounted) {
          setBrand(brandData)
          setSubmissions(subsData)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Failed to load brand workspace.')
          setLoading(false)
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  const handleLaunchTest = (testIndex: number) => {
    const test = DEMO_TEST_CASES[testIndex]
    navigate('/submissions/new', { state: test })
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12 space-y-8">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    )
  }

  if (error || !brand) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-center">
        <h1 className="font-serif text-3xl text-terracotta">Workspace Unavailable</h1>
        <p className="mt-4 text-ink-soft">{error || 'Could not connect to the backend service.'}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-6 px-4 py-2 bg-parchment text-ink text-sm font-medium rounded-sm border border-parchment-deep hover:bg-parchment-deep transition-colors"
        >
          Retry Connection
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 space-y-12">
      {/* Brand Hero & Voice Overview */}
      <section className="bg-ivory border border-parchment-deep p-8 rounded-sm">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="flex items-center gap-3">
              <h1 className="font-serif text-3xl font-bold text-ink">{brand.name}</h1>
              <span className="text-xs uppercase tracking-wider text-sage font-medium px-2 py-0.5 bg-sage-soft rounded-sm border border-sage/20">
                {brand.industry}
              </span>
              <span className="text-xs text-ink-soft px-2 py-0.5 bg-parchment rounded-sm border border-parchment-deep">
                Demo Workspace
              </span>
            </div>
            <p className="text-sm text-ink-soft leading-relaxed">{brand.description}</p>
            <div className="pt-2 text-xs text-ink">
              <span className="font-semibold text-sage uppercase tracking-wider mr-2">Brand Voice:</span>
              <span className="italic">{brand.voice_summary}</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/submissions/new"
              className="inline-flex items-center justify-center px-5 py-2.5 bg-ink text-ivory text-sm font-medium rounded-sm hover:bg-ink-soft transition-colors text-center"
            >
              Submit Content for Review
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Judge Test Launcher */}
      <section className="bg-parchment/50 border border-parchment-deep p-6 rounded-sm space-y-4">
        <div>
          <h2 className="font-serif text-lg font-semibold text-ink">
            Interactive Test Scenarios for Evaluation
          </h2>
          <p className="text-xs text-ink-soft">
            Select an official test case to pre-fill the submission editor and inspect real compliance results instantly.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {DEMO_TEST_CASES.map((tc, index) => (
            <button
              key={tc.id}
              onClick={() => handleLaunchTest(index)}
              className="text-left p-4 bg-ivory border border-parchment-deep hover:border-sage rounded-sm transition-colors space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-ink group-hover:text-sage transition-colors">
                  {tc.label}
                </span>
                <span className="text-xs text-sage font-medium">Load &rarr;</span>
              </div>
              <p className="text-xs text-ink-soft leading-normal">{tc.description}</p>
            </button>
          ))}
        </div>
      </section>

      {/* Approved Brand Knowledge (Guidelines, Facts, Terminology) */}
      <section className="space-y-6">
        <div className="flex items-center justify-between border-b border-parchment-deep pb-3">
          <div>
            <h2 className="font-serif text-2xl font-bold text-ink">Approved Brand Knowledge</h2>
            <p className="text-xs text-ink-soft">
              Deterministic standards and contextual facts against which content is verified.
            </p>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => setActiveTab('guidelines')}
              className={`px-3 py-1.5 text-xs font-medium rounded-sm transition-colors ${
                activeTab === 'guidelines'
                  ? 'bg-ink text-ivory'
                  : 'bg-parchment text-ink-soft hover:text-ink'
              }`}
            >
              Guidelines ({brand.guidelines.length})
            </button>
            <button
              onClick={() => setActiveTab('facts')}
              className={`px-3 py-1.5 text-xs font-medium rounded-sm transition-colors ${
                activeTab === 'facts'
                  ? 'bg-ink text-ivory'
                  : 'bg-parchment text-ink-soft hover:text-ink'
              }`}
            >
              Approved Facts ({brand.facts.length})
            </button>
            <button
              onClick={() => setActiveTab('terms')}
              className={`px-3 py-1.5 text-xs font-medium rounded-sm transition-colors ${
                activeTab === 'terms'
                  ? 'bg-ink text-ivory'
                  : 'bg-parchment text-ink-soft hover:text-ink'
              }`}
            >
              Terminology ({brand.terms.length})
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'guidelines' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {brand.guidelines.map((guide) => (
              <div
                key={guide.id}
                className="bg-ivory border border-parchment-deep p-5 rounded-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-sage bg-sage-soft/40 px-2 py-0.5 rounded-sm border border-sage/20">
                    {guide.id}
                  </span>
                  <SeverityBadge severity={guide.default_severity} />
                </div>
                <h3 className="font-serif text-base font-semibold text-ink">{guide.title}</h3>
                <p className="text-xs text-ink-soft leading-relaxed">{guide.text}</p>
                <div className="pt-2">
                  <CategoryBadge category={guide.category} />
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'facts' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {brand.facts.map((fact) => (
              <div
                key={fact.id}
                className="bg-ivory border border-parchment-deep p-5 rounded-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-sage bg-sage-soft/40 px-2 py-0.5 rounded-sm border border-sage/20">
                    {fact.id}
                  </span>
                  <span className="text-xs text-ink-soft italic">Approved Fact</span>
                </div>
                <p className="text-sm text-ink leading-relaxed font-serif">{fact.statement}</p>
                {fact.source && (
                  <p className="text-xs text-ink-soft pt-1 border-t border-parchment-deep/40">
                    <span className="font-semibold">Source:</span> {fact.source}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'terms' && (
          <div className="grid grid-cols-1 gap-6">
            {brand.terms.map((term) => (
              <div
                key={term.id}
                className="bg-ivory border border-parchment-deep p-6 rounded-sm space-y-4"
              >
                <div className="flex items-center justify-between border-b border-parchment-deep/60 pb-3">
                  <span className="text-xs font-mono font-bold text-sage bg-sage-soft/40 px-2 py-0.5 rounded-sm border border-sage/20">
                    {term.id}
                  </span>
                  {term.related_guideline_id && (
                    <span className="text-xs text-ink-soft">
                      Related: <span className="font-mono text-sage">{term.related_guideline_id}</span>
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="space-y-1.5 p-3 bg-sage-soft/20 rounded-sm border border-sage/20">
                    <span className="text-xs uppercase tracking-wider font-semibold text-sage">
                      Approved Preferred Terminology
                    </span>
                    <p className="font-serif text-sm font-semibold text-ink">
                      "{term.preferred_term}"
                    </p>
                  </div>

                  <div className="space-y-1.5 p-3 bg-terracotta-soft/20 rounded-sm border border-terracotta/20">
                    <span className="text-xs uppercase tracking-wider font-semibold text-terracotta">
                      Prohibited Terminology
                    </span>
                    <p className="font-serif text-sm font-semibold text-ink line-through decoration-terracotta">
                      "{term.prohibited_term}"
                    </p>
                  </div>
                </div>

                {term.notes && (
                  <p className="text-xs text-ink-soft">
                    <span className="font-semibold">Usage note:</span> {term.notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Submissions & Governance History */}
      <section className="space-y-6">
        <div className="flex items-center justify-between border-b border-parchment-deep pb-3">
          <div>
            <h2 className="font-serif text-2xl font-bold text-ink">Submissions & Governance History</h2>
            <p className="text-xs text-ink-soft">
              Active and past content evaluated against brand standards.
            </p>
          </div>

          <Link
            to="/submissions/new"
            className="px-3 py-1.5 text-xs font-medium text-ink bg-parchment border border-parchment-deep rounded-sm hover:bg-parchment-deep transition-colors"
          >
            + New Submission
          </Link>
        </div>

        {submissions.length === 0 ? (
          <div className="text-center py-12 bg-ivory border border-parchment-deep rounded-sm space-y-3">
            <p className="font-serif text-lg text-ink">No submissions yet</p>
            <p className="text-xs text-ink-soft max-w-sm mx-auto">
              Get started by testing one of the demo scenarios above or submitting your own draft marketing content.
            </p>
            <button
              onClick={() => handleLaunchTest(0)}
              className="mt-2 px-4 py-2 bg-ink text-ivory text-xs font-medium rounded-sm hover:bg-ink-soft transition-colors"
            >
              Run Non-Compliant Demo Test
            </button>
          </div>
        ) : (
          <div className="bg-ivory border border-parchment-deep rounded-sm overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-parchment-deep bg-parchment/40 text-xs text-ink-soft font-semibold">
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Workflow Status</th>
                  <th className="py-3 px-4">Compliance Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-parchment-deep/60 text-xs">
                {submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-parchment/20 transition-colors">
                    <td className="py-3.5 px-4 font-serif text-sm font-semibold text-ink">
                      <Link to={`/submissions/${sub.id}`} className="hover:text-sage transition-colors">
                        {sub.title}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 capitalize text-ink-soft">{sub.content_type.replace('_', ' ')}</td>
                    <td className="py-3.5 px-4 font-mono font-medium text-ink-soft">v{sub.current_version_number}</td>
                    <td className="py-3.5 px-4">
                      <SubmissionStatusBadge status={sub.status} />
                    </td>
                    <td className="py-3.5 px-4">
                      <OverallBadge status={sub.latest_overall_status} />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/submissions/${sub.id}`}
                        className="inline-flex items-center px-2.5 py-1 text-xs font-medium text-ink bg-parchment border border-parchment-deep rounded-sm hover:bg-parchment-deep transition-colors"
                      >
                        Inspect &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
