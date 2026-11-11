/**
 * Brand Creation and Profile Editing Modal.
 * Used by Brand Managers to establish and update brand workspaces.
 */

import { useState } from 'react'
import { api, ApiError } from '../api/client'
import type { BrandDetail, BrandSummary } from '../api/types'
import { useAuth } from '../context/AuthContext'

interface BrandModalProps {
  isOpen: boolean
  onClose: () => void
  brandToEdit?: BrandDetail | null
  onBrandSaved?: (brand: BrandDetail) => void
}

export function BrandModal({ isOpen, onClose, brandToEdit, onBrandSaved }: BrandModalProps) {
  const { switchBrand, refreshBrands } = useAuth()
  const [name, setName] = useState(brandToEdit?.name || '')
  const [industry, setIndustry] = useState(brandToEdit?.industry || '')
  const [description, setDescription] = useState(brandToEdit?.description || '')
  const [voiceSummary, setVoiceSummary] = useState(brandToEdit?.voice_summary || '')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const isEditing = Boolean(brandToEdit)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      let saved: BrandDetail
      if (isEditing && brandToEdit) {
        saved = await api.updateBrand(brandToEdit.id, {
          name: name.trim(),
          industry: industry.trim(),
          description: description.trim(),
          voice_summary: voiceSummary.trim(),
        })
      } else {
        saved = await api.createBrand({
          name: name.trim(),
          industry: industry.trim(),
          description: description.trim(),
          voice_summary: voiceSummary.trim(),
        })
        switchBrand(saved as unknown as BrandSummary)
      }

      await refreshBrands()
      if (onBrandSaved) onBrandSaved(saved)
      onClose()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(isEditing ? 'Failed to update brand profile.' : 'Failed to create brand workspace.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg bg-ivory border border-parchment-deep rounded-sm shadow-xl overflow-hidden animate-fadeIn">
        <div className="px-6 pt-6 pb-4 border-b border-parchment-deep flex items-baseline justify-between">
          <div>
            <h2 className="font-serif text-xl font-bold text-ink">
              {isEditing ? `Edit Brand: ${brandToEdit?.name}` : 'New Brand Workspace'}
            </h2>
            <p className="text-xs text-ink-soft mt-1">
              {isEditing
                ? 'Update brand positioning, industry, and voice directives.'
                : 'Establish an independent brand governance profile in your organisation.'}
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

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                Brand Name
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Velveteen Botanicals"
                className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                Industry
              </label>
              <input
                type="text"
                required
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g. Skincare, Beverages, Fintech"
                className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
              Description & Positioning
            </label>
            <textarea
              rows={3}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the brand, target audience, and primary products..."
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage resize-y"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
              Brand Voice Summary
            </label>
            <textarea
              rows={2}
              required
              value={voiceSummary}
              onChange={(e) => setVoiceSummary(e.target.value)}
              placeholder="e.g. Friendly, reassuring, and realistic. Evidence-backed claims only..."
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage resize-y"
            />
          </div>

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
              {isSubmitting ? 'Saving...' : isEditing ? 'Update Brand' : 'Create Brand Workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
