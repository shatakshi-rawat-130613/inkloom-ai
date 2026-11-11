/**
 * Brand Workspace page.
 * Displays approved guidelines, facts, terminology, visual assets, and submission history.
 * Supports complete multi-brand workspace management: brand creation, editing,
 * guideline authoring, fact verification, terminology controls, and visual asset configuration.
 */

import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { BrandAssetResponse, BrandDetail, SubmissionListItem } from '../api/types'
import { Skeleton } from '../components/Skeleton'
import { CategoryBadge, OverallBadge, SeverityBadge, SubmissionStatusBadge } from '../components/StatusBadge'
import { BrandModal } from '../components/BrandModal'
import { KnowledgeModal } from '../components/KnowledgeModal'
import { useAuth } from '../context/AuthContext'
import { DEMO_TEST_CASES } from '../data/demoTestCases'

type TabType = 'guidelines' | 'facts' | 'terms' | 'assets'

export function WorkspacePage() {
  const navigate = useNavigate()
  const { activeBrand, user } = useAuth()

  const [brand, setBrand] = useState<BrandDetail | null>(null)
  const [assets, setAssets] = useState<BrandAssetResponse[]>([])
  const [submissions, setSubmissions] = useState<SubmissionListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('guidelines')

  // Modals
  const [isEditBrandOpen, setIsEditBrandOpen] = useState(false)
  const [isKnowledgeModalOpen, setIsKnowledgeModalOpen] = useState(false)
  const [knowledgeModalType, setKnowledgeModalType] = useState<'guideline' | 'fact' | 'term' | 'asset'>('guideline')

  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    let mounted = true
    const targetSlugOrId = activeBrand ? activeBrand.id : 'lumacare'

    Promise.all([
      api.getBrand(targetSlugOrId),
      api.listSubmissions(activeBrand?.id),
    ])
      .then(([brandData, subsData]) => {
        if (mounted) {
          setBrand(brandData)
          setSubmissions(subsData)
          api.listBrandAssets(brandData.id)
            .then((assetList) => {
              if (mounted) setAssets(assetList)
            })
            .catch(() => {
              if (mounted) setAssets([])
            })
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
  }, [activeBrand])

  const handleLaunchTest = (testIndex: number) => {
    const test = DEMO_TEST_CASES[testIndex]
    navigate('/submissions/new', { state: test })
  }

  const openAddKnowledge = (tab: TabType) => {
    if (tab === 'guidelines') setKnowledgeModalType('guideline')
    else if (tab === 'facts') setKnowledgeModalType('fact')
    else if (tab === 'terms') setKnowledgeModalType('term')
    else if (tab === 'assets') setKnowledgeModalType('asset')
    setIsKnowledgeModalOpen(true)
  }

  const handleDeleteGuideline = async (code: string) => {
    if (!brand || !confirm(`Deactivate guideline ${code}?`)) return
    try {
      const updated = await api.deleteGuideline(brand.id, code)
      setBrand(updated)
    } catch {
      alert('Failed to deactivate guideline.')
    }
  }

  const handleDeleteFact = async (code: string) => {
    if (!brand || !confirm(`Deactivate fact ${code}?`)) return
    try {
      const updated = await api.deleteFact(brand.id, code)
      setBrand(updated)
    } catch {
      alert('Failed to deactivate fact.')
    }
  }

  const handleDeleteTerm = async (code: string) => {
    if (!brand || !confirm(`Deactivate term ${code}?`)) return
    try {
      const updated = await api.deleteTerm(brand.id, code)
      setBrand(updated)
    } catch {
      alert('Failed to deactivate term.')
    }
  }

  const handleDeleteAsset = async (assetId: string) => {
    if (!brand || !confirm('Deactivate this visual asset?')) return
    try {
      const updatedList = await api.deleteBrandAsset(brand.id, assetId)
      setAssets(updatedList)
    } catch {
      alert('Failed to deactivate visual asset.')
    }
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
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="p-6 bg-terracotta-soft/30 border border-terracotta/40 rounded-sm space-y-2">
          <h2 className="font-serif text-lg font-bold text-terracotta">Unable to Load Workspace</h2>
          <p className="text-sm text-ink-soft">{error || 'Brand workspace not found.'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 space-y-12">
      {/* Brand Hero & Workspace Overview */}
      <section className="border-b border-parchment-deep pb-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="flex items-center space-x-2">
              <span className="text-xs uppercase tracking-widest text-sage font-medium">
                Workspace
              </span>
              <span className="text-xs text-ink-soft">/</span>
              <span className="text-xs font-semibold text-ink-soft">{brand.industry}</span>
              {brand.is_demo && (
                <span className="text-[10px] uppercase tracking-wider font-semibold text-ink-soft bg-parchment px-2 py-0.5 rounded-sm border border-parchment-deep">
                  Fictional Demo Brand
                </span>
              )}
            </div>

            <div className="flex items-center space-x-3">
              <h1 className="font-serif text-4xl font-bold tracking-tight text-ink">
                {brand.name}
              </h1>
              {isAdmin && !brand.is_demo && (
                <button
                  type="button"
                  onClick={() => setIsEditBrandOpen(true)}
                  className="px-2.5 py-1 text-xs font-medium text-ink bg-parchment border border-parchment-deep rounded-sm hover:border-sage transition-colors"
                >
                  Edit Profile
                </button>
              )}
            </div>

            <p className="text-sm text-ink-soft leading-relaxed">
              {brand.description}
            </p>

            <div className="pt-2 text-xs text-ink-soft flex items-center space-x-2">
              <span className="font-semibold text-ink">Brand Voice:</span>
              <span className="italic">{brand.voice_summary}</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/submissions/new"
              className="inline-flex items-center justify-center px-5 py-2.5 bg-ink text-ivory text-sm font-medium rounded-sm hover:bg-sage transition-colors text-center"
            >
              Submit Content for Review
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Judge Test Launcher (shown on demo brand) */}
      {brand.is_demo && (
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
      )}

      {/* Approved Brand Standards (Guidelines, Facts, Terminology, Visual Assets) */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-parchment-deep pb-3">
          <div>
            <h2 className="font-serif text-2xl font-bold text-ink">Approved Brand Standards</h2>
            <p className="text-xs text-ink-soft">
              Deterministic guidelines, verified facts, approved terminology, and visual asset palette.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 overflow-x-auto pb-1 sm:pb-0">
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
                Facts ({brand.facts.length})
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
              <button
                onClick={() => setActiveTab('assets')}
                className={`px-3 py-1.5 text-xs font-medium rounded-sm transition-colors ${
                  activeTab === 'assets'
                    ? 'bg-ink text-ivory'
                    : 'bg-parchment text-ink-soft hover:text-ink'
                }`}
              >
                Visual Assets ({assets.length})
              </button>
            </div>

            {isAdmin && !brand.is_demo && (
              <button
                type="button"
                onClick={() => openAddKnowledge(activeTab)}
                className="px-3 py-1.5 text-xs font-semibold bg-sage text-ivory rounded-sm hover:bg-sage/90 transition-colors shrink-0"
              >
                + Add {activeTab.slice(0, -1)}
              </button>
            )}
          </div>
        </div>

        {/* Tab Content: Guidelines */}
        {activeTab === 'guidelines' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {brand.guidelines.map((guide) => (
              <div
                key={guide.id}
                className="bg-ivory border border-parchment-deep p-5 rounded-sm space-y-3 relative group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-sage bg-sage-soft/40 px-2 py-0.5 rounded-sm border border-sage/20">
                    {guide.id}
                  </span>
                  <div className="flex items-center space-x-2">
                    <SeverityBadge severity={guide.default_severity} />
                    {isAdmin && !brand.is_demo && (
                      <button
                        type="button"
                        onClick={() => handleDeleteGuideline(guide.id)}
                        className="text-ink-soft hover:text-terracotta text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Deactivate rule"
                      >
                        ✕
                      </button>
                    )}
                  </div>
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

        {/* Tab Content: Facts */}
        {activeTab === 'facts' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {brand.facts.map((fact) => (
              <div
                key={fact.id}
                className="bg-ivory border border-parchment-deep p-5 rounded-sm space-y-3 relative group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-sage bg-sage-soft/40 px-2 py-0.5 rounded-sm border border-sage/20">
                    {fact.id}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-ink-soft italic">Approved Fact</span>
                    {isAdmin && !brand.is_demo && (
                      <button
                        type="button"
                        onClick={() => handleDeleteFact(fact.id)}
                        className="text-ink-soft hover:text-terracotta text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Deactivate fact"
                      >
                        ✕
                      </button>
                    )}
                  </div>
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

        {/* Tab Content: Terminology */}
        {activeTab === 'terms' && (
          <div className="grid grid-cols-1 gap-6">
            {brand.terms.map((term) => (
              <div
                key={term.id}
                className="bg-ivory border border-parchment-deep p-6 rounded-sm space-y-4 relative group"
              >
                <div className="flex items-center justify-between border-b border-parchment-deep/60 pb-3">
                  <span className="text-xs font-mono font-bold text-sage bg-sage-soft/40 px-2 py-0.5 rounded-sm border border-sage/20">
                    {term.id}
                  </span>
                  <div className="flex items-center space-x-3">
                    {term.related_guideline_id && (
                      <span className="text-xs text-ink-soft">
                        Related: <span className="font-mono text-sage">{term.related_guideline_id}</span>
                      </span>
                    )}
                    {isAdmin && !brand.is_demo && (
                      <button
                        type="button"
                        onClick={() => handleDeleteTerm(term.id)}
                        className="text-ink-soft hover:text-terracotta text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Deactivate term"
                      >
                        ✕
                      </button>
                    )}
                  </div>
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

        {/* Tab Content: Visual Assets */}
        {activeTab === 'assets' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {assets.length === 0 ? (
              <div className="col-span-2 text-center py-8 bg-ivory border border-parchment-deep rounded-sm">
                <p className="text-xs text-ink-soft">No visual brand assets configured for this workspace.</p>
              </div>
            ) : (
              assets.map((asset) => (
                <div
                  key={asset.id}
                  className="bg-ivory border border-parchment-deep p-6 rounded-sm space-y-4 relative group"
                >
                  <div className="flex items-center justify-between border-b border-parchment-deep pb-2">
                    <h3 className="font-serif text-base font-bold text-ink">{asset.name}</h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 bg-parchment rounded text-sage border border-parchment-deep">
                        {asset.asset_type.replace('_', ' ')}
                      </span>
                      {isAdmin && !brand.is_demo && (
                        <button
                          type="button"
                          onClick={() => handleDeleteAsset(asset.id)}
                          className="text-ink-soft hover:text-terracotta text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Deactivate asset"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </div>

                  {asset.asset_type === 'color_palette' && (
                    <div className="space-y-3">
                      <div className="text-xs text-ink-soft">Approved Brand Color Palette:</div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {((asset.asset_metadata.colors as Array<{ name: string; hex: string; role: string }>) || []).map(
                          (c) => (
                            <div
                              key={c.hex}
                              className="p-2 border border-parchment-deep rounded-sm flex items-center space-x-2"
                            >
                              <div
                                className="w-6 h-6 rounded-xs border border-ink/20 shadow-inner shrink-0"
                                style={{ backgroundColor: c.hex }}
                              />
                              <div className="overflow-hidden">
                                <div className="text-xs font-bold text-ink truncate">{c.name}</div>
                                <div className="text-[10px] font-mono text-ink-soft">{c.hex}</div>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {asset.asset_type === 'logo' && (
                    <div className="space-y-2 text-xs text-ink-soft">
                      <div>
                        <span className="font-semibold text-ink">Wordmark Text:</span>{' '}
                        {String(asset.asset_metadata.text || '')}
                      </div>
                      <div>
                        <span className="font-semibold text-ink">Aspect Ratio:</span>{' '}
                        {String(asset.asset_metadata.aspect_ratio || '')}
                      </div>
                      <div>
                        <span className="font-semibold text-ink">Clearance Padding:</span>{' '}
                        {String(asset.asset_metadata.min_clearance_px || 24)}px
                      </div>
                    </div>
                  )}

                  {asset.asset_type === 'visual_guideline' && (
                    <div className="space-y-2 text-xs text-ink-soft">
                      <div>
                        <span className="font-semibold text-ink">Imagery Standard:</span>{' '}
                        {String(asset.asset_metadata.imagery_style || '')}
                      </div>
                      <div>
                        <span className="font-semibold text-ink">Min Contrast:</span>{' '}
                        {String(asset.asset_metadata.min_contrast_ratio || 4.5)}:1
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
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
            <p className="text-sm text-ink-soft font-serif">
              No submissions recorded yet for this workspace.
            </p>
            <Link
              to="/submissions/new"
              className="inline-block px-4 py-2 bg-ink text-ivory text-xs font-semibold rounded-sm hover:bg-sage transition-colors"
            >
              Create First Submission
            </Link>
          </div>
        ) : (
          <div className="bg-ivory border border-parchment-deep rounded-sm divide-y divide-parchment-deep overflow-hidden">
            {submissions.map((sub) => (
              <div
                key={sub.id}
                onClick={() => navigate(`/submissions/${sub.id}`)}
                className="p-5 hover:bg-parchment/40 transition-colors cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-serif text-base font-semibold text-ink hover:text-sage transition-colors">
                      {sub.title}
                    </h3>
                    <span className="text-xs font-mono text-ink-soft">
                      v{sub.current_version_number}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3 text-xs text-ink-soft">
                    <span>{sub.author_name}</span>
                    <span>&bull;</span>
                    <span className="capitalize">{sub.content_type.replace('_', ' ')}</span>
                    <span>&bull;</span>
                    <span>{new Date(sub.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  {sub.latest_overall_status && (
                    <OverallBadge status={sub.latest_overall_status} />
                  )}
                  <SubmissionStatusBadge status={sub.status} />
                  <span className="text-xs text-ink-soft">&rarr;</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Edit Brand Profile Modal */}
      {brand && (
        <BrandModal
          isOpen={isEditBrandOpen}
          onClose={() => setIsEditBrandOpen(false)}
          brandToEdit={brand}
          onBrandSaved={(updated) => setBrand(updated)}
        />
      )}

      {/* Add Knowledge Entry Modal */}
      {brand && (
        <KnowledgeModal
          isOpen={isKnowledgeModalOpen}
          onClose={() => setIsKnowledgeModalOpen(false)}
          brand={brand}
          type={knowledgeModalType}
          onSaved={(updated) => {
            setBrand(updated)
            api.listBrandAssets(brand.id).then((l) => setAssets(l)).catch(() => {})
          }}
        />
      )}
    </div>
  )
}
