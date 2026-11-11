/**
 * Brand Knowledge & Visual Asset Configuration Modal.
 * Enables Brand Managers to author and append guidelines, verified facts,
 * terminology constraints, and visual assets directly to the brand workspace.
 */

import { useState } from 'react'
import { api, ApiError } from '../api/client'
import type {
  BrandDetail,
  FindingCategory,
  Severity,
} from '../api/types'

type KnowledgeType = 'guideline' | 'fact' | 'term' | 'asset'

interface KnowledgeModalProps {
  isOpen: boolean
  onClose: () => void
  brand: BrandDetail
  type: KnowledgeType
  onSaved: (updatedBrand: BrandDetail) => void
}

export function KnowledgeModal({ isOpen, onClose, brand, type, onSaved }: KnowledgeModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Guideline fields
  const [guideCode, setGuideCode] = useState(`GUIDE-${String(brand.guidelines.length + 1).padStart(3, '0')}`)
  const [guideTitle, setGuideTitle] = useState('')
  const [guideText, setGuideText] = useState('')
  const [guideCategory, setGuideCategory] = useState<FindingCategory>('outcome_claim')
  const [guideSeverity, setGuideSeverity] = useState<Severity>('high')

  // Fact fields
  const [factCode, setFactCode] = useState(`FACT-${String(brand.facts.length + 1).padStart(3, '0')}`)
  const [factStatement, setFactStatement] = useState('')
  const [factSource, setFactSource] = useState('')

  // Term fields
  const [termCode, setTermCode] = useState(`TERM-${String(brand.terms.length + 1).padStart(3, '0')}`)
  const [preferredTerm, setPreferredTerm] = useState('')
  const [prohibitedTerm, setProhibitedTerm] = useState('')
  const [termNotes, setTermNotes] = useState('')
  const [relatedGuideCode, setRelatedGuideCode] = useState(brand.guidelines[0]?.id || '')

  // Asset fields
  const [assetType, setAssetType] = useState('color_palette')
  const [assetName, setAssetName] = useState('')
  const [colorHex1, setColorHex1] = useState('#FDFBF7')
  const [colorName1, setColorName1] = useState('Primary Ivory')
  const [colorHex2, setColorHex2] = useState('#1C1917')
  const [colorName2, setColorName2] = useState('Primary Ink')
  const [logoWordmark, setLogoWordmark] = useState(brand.name)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      let updated: BrandDetail = brand

      if (type === 'guideline') {
        updated = await api.addGuideline(brand.id, {
          code: guideCode.trim().toUpperCase(),
          title: guideTitle.trim(),
          rule_text: guideText.trim(),
          category: guideCategory,
          default_severity: guideSeverity,
        })
      } else if (type === 'fact') {
        updated = await api.addFact(brand.id, {
          code: factCode.trim().toUpperCase(),
          statement: factStatement.trim(),
          source: factSource.trim() || null,
        })
      } else if (type === 'term') {
        updated = await api.addTerm(brand.id, {
          code: termCode.trim().toUpperCase(),
          preferred_term: preferredTerm.trim() || null,
          prohibited_term: prohibitedTerm.trim() || null,
          notes: termNotes.trim() || null,
          related_guideline_code: relatedGuideCode.trim() || null,
        })
      } else if (type === 'asset') {
        let meta: Record<string, unknown> = {}
        if (assetType === 'color_palette') {
          meta = {
            colors: [
              { name: colorName1, hex: colorHex1, role: 'primary' },
              { name: colorName2, hex: colorHex2, role: 'secondary' },
            ],
            max_color_delta_e: 25.0,
          }
        } else if (assetType === 'logo') {
          meta = {
            text: logoWordmark,
            aspect_ratio: '3:1',
            min_width_px: 120,
            min_clearance_px: 24,
            acceptable_variants: [logoWordmark, logoWordmark.toUpperCase(), logoWordmark.toLowerCase()],
          }
        } else {
          meta = {
            min_contrast_ratio: 4.5,
            imagery_style: 'Clean, authentic, natural lighting.',
          }
        }

        await api.createBrandAsset(brand.id, {
          asset_type: assetType,
          name: assetName.trim() || `${brand.name} ${assetType.replace('_', ' ')}`,
          asset_metadata: meta,
        })
        updated = await api.getBrand(brand.id)
      }

      onSaved(updated)
      onClose()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to save brand knowledge entry.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const titles: Record<KnowledgeType, string> = {
    guideline: 'Add Brand Guideline',
    fact: 'Add Approved Fact',
    term: 'Add Terminology Rule',
    asset: 'Add Visual Brand Asset',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg bg-ivory border border-parchment-deep rounded-sm shadow-xl overflow-hidden animate-fadeIn">
        <div className="px-6 pt-6 pb-4 border-b border-parchment-deep flex items-baseline justify-between">
          <div>
            <h2 className="font-serif text-xl font-bold text-ink">{titles[type]}</h2>
            <p className="text-xs text-ink-soft mt-1">
              Brand: <strong className="text-ink">{brand.name}</strong>
            </p>
          </div>
          <button onClick={onClose} className="text-ink-soft hover:text-ink text-sm px-2 py-1">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-terracotta/10 border border-terracotta/30 text-terracotta text-xs rounded-sm">
              {error}
            </div>
          )}

          {/* Guideline Fields */}
          {type === 'guideline' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                    Guideline Code
                  </label>
                  <input
                    type="text"
                    required
                    value={guideCode}
                    onChange={(e) => setGuideCode(e.target.value)}
                    className="w-full px-3 py-2 text-sm font-mono bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                    Severity
                  </label>
                  <select
                    value={guideSeverity}
                    onChange={(e) => setGuideSeverity(e.target.value as Severity)}
                    className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                    <option value="informational">Informational</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Category
                </label>
                <select
                  value={guideCategory}
                  onChange={(e) => setGuideCategory(e.target.value as FindingCategory)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                >
                  <option value="outcome_claim">Outcome Claim</option>
                  <option value="tone">Tone</option>
                  <option value="factual_consistency">Factual Consistency</option>
                  <option value="terminology">Terminology</option>
                  <option value="timeframe">Timeframe</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Rule Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. No absolute cure promises"
                  value={guideTitle}
                  onChange={(e) => setGuideTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Rule Text & Directive
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Do not state or imply guaranteed clinical or aesthetic outcomes..."
                  value={guideText}
                  onChange={(e) => setGuideText(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage resize-y"
                />
              </div>
            </>
          )}

          {/* Fact Fields */}
          {type === 'fact' && (
            <>
              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Fact Code
                </label>
                <input
                  type="text"
                  required
                  value={factCode}
                  onChange={(e) => setFactCode(e.target.value)}
                  className="w-full px-3 py-2 text-sm font-mono bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Factual Statement
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="The formulation contains 2% niacinamide designed for gentle hydration."
                  value={factStatement}
                  onChange={(e) => setFactStatement(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage resize-y"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Source / Document Citation
                </label>
                <input
                  type="text"
                  placeholder="e.g. Clinical Trial Report CT-2025-A"
                  value={factSource}
                  onChange={(e) => setFactSource(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                />
              </div>
            </>
          )}

          {/* Term Fields */}
          {type === 'term' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                    Term Code
                  </label>
                  <input
                    type="text"
                    required
                    value={termCode}
                    onChange={(e) => setTermCode(e.target.value)}
                    className="w-full px-3 py-2 text-sm font-mono bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                    Related Guideline
                  </label>
                  <select
                    value={relatedGuideCode}
                    onChange={(e) => setRelatedGuideCode(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage font-mono"
                  >
                    <option value="">None</option>
                    {brand.guidelines.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.id}: {g.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-sage uppercase tracking-wider mb-1">
                    Preferred Term
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. supports clearer-looking skin"
                    value={preferredTerm}
                    onChange={(e) => setPreferredTerm(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-terracotta uppercase tracking-wider mb-1">
                    Prohibited Term
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. cures all blemishes instantly"
                    value={prohibitedTerm}
                    onChange={(e) => setProhibitedTerm(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Usage Notes
                </label>
                <input
                  type="text"
                  placeholder="Always prefer supportive phrasing over definitive medical claims."
                  value={termNotes}
                  onChange={(e) => setTermNotes(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                />
              </div>
            </>
          )}

          {/* Visual Asset Fields */}
          {type === 'asset' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                    Asset Type
                  </label>
                  <select
                    value={assetType}
                    onChange={(e) => setAssetType(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  >
                    <option value="color_palette">Color Palette</option>
                    <option value="logo">Approved Logo</option>
                    <option value="visual_guideline">Visual Guideline</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                    Asset Label
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Primary Identity Palette"
                    value={assetName}
                    onChange={(e) => setAssetName(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>
              </div>

              {assetType === 'color_palette' && (
                <div className="space-y-3 p-3 bg-parchment/40 border border-parchment-deep rounded-sm">
                  <span className="text-xs font-semibold text-ink uppercase tracking-wider">
                    Palette Swatches
                  </span>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] text-ink-soft">Color 1 (Hex & Name)</label>
                      <div className="flex space-x-2 mt-1">
                        <input
                          type="color"
                          value={colorHex1}
                          onChange={(e) => setColorHex1(e.target.value)}
                          className="w-8 h-8 rounded border border-ink/20 p-0 cursor-pointer"
                        />
                        <input
                          type="text"
                          value={colorName1}
                          onChange={(e) => setColorName1(e.target.value)}
                          className="w-full px-2 py-1 text-xs bg-ivory border border-parchment-deep rounded-sm"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-[10px] text-ink-soft">Color 2 (Hex & Name)</label>
                      <div className="flex space-x-2 mt-1">
                        <input
                          type="color"
                          value={colorHex2}
                          onChange={(e) => setColorHex2(e.target.value)}
                          className="w-8 h-8 rounded border border-ink/20 p-0 cursor-pointer"
                        />
                        <input
                          type="text"
                          value={colorName2}
                          onChange={(e) => setColorName2(e.target.value)}
                          className="w-full px-2 py-1 text-xs bg-ivory border border-parchment-deep rounded-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {assetType === 'logo' && (
                <div>
                  <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                    Wordmark Text
                  </label>
                  <input
                    type="text"
                    required
                    value={logoWordmark}
                    onChange={(e) => setLogoWordmark(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>
              )}
            </>
          )}

          <div className="pt-3 flex justify-end space-x-3 border-t border-parchment-deep">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-ink-soft bg-parchment border border-parchment-deep rounded-sm hover:text-ink"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 bg-ink text-ivory text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-sage transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Add to Brand Standards'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
