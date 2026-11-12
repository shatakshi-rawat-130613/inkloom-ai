/**
 * Brand Selection and Access-State Page.
 * Displayed when an authenticated user has multiple authorised brand workspaces,
 * when a stale brand ID is discarded, or when an organisation has zero brand workspaces.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BrandModal } from '../components/BrandModal'
import { useAuth } from '../context/AuthContext'

export function SelectBrandPage() {
  const navigate = useNavigate()
  const { user, availableBrands, switchBrand, logout, refreshBrands } = useAuth()
  const [isCreateBrandOpen, setIsCreateBrandOpen] = useState(false)

  const isAdmin = user?.role === 'admin'

  const handleSelect = (brandId: string) => {
    const brand = availableBrands.find((b) => b.id === brandId)
    if (brand) {
      switchBrand(brand)
      navigate('/workspace')
    }
  }

  const handleBrandCreated = async () => {
    setIsCreateBrandOpen(false)
    const res = await refreshBrands(user)
    if (res.activeBrand) {
      navigate('/workspace')
    }
  }

  return (
    <div className="min-h-[85vh] bg-ivory py-16 px-6 flex flex-col justify-center items-center">
      <div className="w-full max-w-3xl space-y-8">
        {/* Header & User Context */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-parchment rounded-sm border border-parchment-deep text-xs font-medium text-ink-soft">
            <span>Organisation:</span>
            <span className="font-semibold text-ink">{user?.organisation_name || 'Personal'}</span>
            <span className="h-3 w-px bg-parchment-deep" />
            <span className="capitalize text-sage font-semibold">{user?.role === 'admin' ? 'Brand Manager' : user?.role || 'Member'}</span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl font-bold text-ink">
            {availableBrands.length === 0 ? 'No Brand Workspaces Found' : 'Select Brand Workspace'}
          </h1>
          <p className="text-sm sm:text-base text-ink-soft max-w-xl mx-auto">
            {availableBrands.length === 0
              ? 'Your organisation currently has no registered brand workspaces.'
              : 'Choose the authorised brand workspace you wish to manage, create content for, or review in this session.'}
          </p>
        </div>

        {/* Content Box */}
        {availableBrands.length === 0 ? (
          <div className="bg-parchment rounded-sm border border-parchment-deep p-8 text-center space-y-6">
            <div className="h-12 w-12 rounded-full bg-sand/40 border border-sand mx-auto flex items-center justify-center text-ink font-serif text-xl font-bold">
              !
            </div>
            <div className="space-y-2 max-w-md mx-auto">
              <h2 className="font-serif text-lg font-bold text-ink">
                {isAdmin ? 'Create your first brand workspace' : 'Awaiting brand assignment'}
              </h2>
              <p className="text-xs text-ink-soft leading-relaxed">
                {isAdmin
                  ? 'As the Brand Manager for your organisation, you can establish independent brand guidelines, clinical/factual references, and terminology rules.'
                  : 'Your account is active, but no brand workspace has been created for your organisation yet. Please contact your Brand Manager.'}
              </p>
            </div>

            {isAdmin && (
              <button
                type="button"
                onClick={() => setIsCreateBrandOpen(true)}
                className="inline-flex items-center px-5 py-2.5 bg-terracotta text-ivory text-xs font-semibold rounded-sm hover:bg-terracotta-dark transition-colors shadow-sm"
              >
                + Create First Brand Workspace
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableBrands.map((b) => (
                <div
                  key={b.id}
                  onClick={() => handleSelect(b.id)}
                  className="bg-parchment hover:bg-parchment-deep/40 rounded-sm border border-parchment-deep hover:border-sage p-6 transition-all cursor-pointer group flex flex-col justify-between space-y-4 shadow-sm"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-sage bg-sage/10 px-2 py-0.5 rounded-sm border border-sage/20">
                        {b.industry}
                      </span>
                      {b.is_demo && (
                        <span className="text-[10px] font-medium text-ochre bg-ochre-soft px-1.5 py-0.5 rounded-sm">
                          Demo Brand
                        </span>
                      )}
                    </div>
                    <h3 className="font-serif text-xl font-bold text-ink group-hover:text-plum transition-colors">
                      {b.name}
                    </h3>
                    <p className="text-xs text-ink-soft line-clamp-3 leading-relaxed">
                      {b.description}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-parchment-deep/60 flex items-center justify-between text-xs font-semibold text-terracotta group-hover:text-terracotta-dark">
                    <span>Enter Workspace</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </div>
              ))}
            </div>

            {isAdmin && (
              <div className="pt-4 text-center">
                <button
                  type="button"
                  onClick={() => setIsCreateBrandOpen(true)}
                  className="text-xs font-semibold text-sage hover:text-ink transition-colors underline underline-offset-4"
                >
                  + Add another brand workspace to {user?.organisation_name || 'organisation'}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Footer actions */}
        <div className="pt-6 border-t border-parchment-deep flex items-center justify-between text-xs text-ink-soft">
          <div>
            Logged in as <span className="font-semibold text-ink">{user?.display_name}</span> ({user?.email})
          </div>
          <button
            type="button"
            onClick={logout}
            className="text-xs font-medium text-ink-soft hover:text-terracotta transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>

      <BrandModal
        isOpen={isCreateBrandOpen}
        onClose={() => setIsCreateBrandOpen(false)}
        onBrandSaved={handleBrandCreated}
      />
    </div>
  )
}
