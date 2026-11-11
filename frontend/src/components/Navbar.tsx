/**
 * Application Navigation Bar.
 * Clean, editorial, typography-driven header with service health indicator,
 * active brand workspace switcher, team management, and role-based user session control.
 */

import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import type { HealthResponse } from '../api/types'
import { useAuth } from '../context/AuthContext'
import { AuthModal } from './AuthModal'
import { BrandModal } from './BrandModal'
import { TeamModal } from './TeamModal'

export function Navbar() {
  const location = useLocation()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [isAuthOpen, setIsAuthOpen] = useState(false)
  const [isBrandModalOpen, setIsBrandModalOpen] = useState(false)
  const [isTeamModalOpen, setIsTeamModalOpen] = useState(false)

  const { user, logout, activeBrand, availableBrands, switchBrand } = useAuth()

  useEffect(() => {
    let mounted = true
    api.getHealth()
      .then((data) => {
        if (mounted) setHealth(data)
      })
      .catch(() => {
        if (mounted) setHealth(null)
      })
    return () => {
      mounted = false
    }
  }, [])

  const navLinks = [
    { to: '/', label: 'Workspace' },
    { to: '/submissions/new', label: 'Submit Content' },
    { to: '/terms', label: 'Terms' },
    { to: '/privacy', label: 'Privacy' },
  ]

  const getRoleLabel = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'Brand Manager'
      case 'editor':
        return 'Creator'
      case 'reviewer':
        return 'Reviewer'
      default:
        return 'Guest'
    }
  }

  const isAdmin = user?.role === 'admin'

  return (
    <>
      <header className="border-b border-parchment-deep bg-ivory/95 sticky top-0 z-20 backdrop-blur-none">
        <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
          {/* Brand identity & Workspace switcher */}
          <div className="flex items-center space-x-3 sm:space-x-5">
            <Link to="/" className="flex items-baseline space-x-2 group">
              <span className="font-serif text-2xl font-bold tracking-tight text-ink group-hover:text-sage transition-colors">
                Inkloom AI
              </span>
              <span className="text-xs uppercase tracking-widest text-sage font-medium">
                Brand Governance
              </span>
            </Link>

            <span className="hidden sm:inline-block h-4 w-px bg-parchment-deep" />

            {/* Brand Switcher & Add Brand Button */}
            <div className="hidden sm:inline-flex items-center space-x-2">
              {availableBrands.length > 1 ? (
                <div className="inline-flex items-center">
                  <label htmlFor="brand-switcher" className="sr-only">Active Brand</label>
                  <select
                    id="brand-switcher"
                    value={activeBrand?.id || ''}
                    onChange={(e) => {
                      const sel = availableBrands.find((b) => b.id === e.target.value)
                      if (sel) switchBrand(sel)
                    }}
                    className="px-2 py-1 text-xs text-ink font-medium bg-parchment rounded-sm border border-parchment-deep focus:outline-none focus:border-sage"
                  >
                    {availableBrands.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name} {b.is_demo ? '(Demo)' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 text-xs text-ink-soft bg-parchment rounded-sm border border-parchment-deep">
                  Workspace: {activeBrand ? activeBrand.name : 'LumaCare Demo'}
                </span>
              )}

              {isAdmin && (
                <button
                  type="button"
                  onClick={() => setIsBrandModalOpen(true)}
                  title="Create new brand in your organisation"
                  className="px-2 py-1 text-[11px] font-semibold text-sage bg-sage/10 border border-sage/30 rounded-sm hover:bg-sage hover:text-ivory transition-colors"
                >
                  + Brand
                </button>
              )}
            </div>
          </div>

          {/* Navigation links, auth controls & health status */}
          <div className="flex items-center space-x-3 sm:space-x-5">
            <nav className="flex items-center space-x-1 sm:space-x-3">
              {navLinks.map((link) => {
                const isActive = location.pathname === link.to
                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`px-2.5 py-1 text-xs sm:text-sm font-medium transition-colors rounded-sm ${
                      isActive
                        ? 'text-ink bg-parchment border border-parchment-deep'
                        : 'text-ink-soft hover:text-ink hover:bg-parchment/60'
                    }`}
                  >
                    {link.label}
                  </Link>
                )
              })}
            </nav>

            {/* User Session & Team Control */}
            <div className="flex items-center pl-2 sm:pl-3 border-l border-parchment-deep space-x-2">
              {user ? (
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsTeamModalOpen(true)}
                    className="px-2 py-1 text-xs font-medium text-ink bg-parchment border border-parchment-deep rounded-sm hover:border-sage transition-colors"
                  >
                    Team
                  </button>

                  <div className="text-right hidden md:block">
                    <div className="text-xs font-semibold text-ink leading-tight">
                      {user.display_name}
                    </div>
                    <div className="text-[10px] text-sage font-medium uppercase tracking-wider">
                      {getRoleLabel(user.role)}
                    </div>
                  </div>

                  <button
                    onClick={logout}
                    className="px-2.5 py-1 text-xs font-medium text-ink-soft bg-parchment border border-parchment-deep rounded-sm hover:text-ink hover:bg-parchment-deep transition-colors"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsAuthOpen(true)}
                  className="px-3 py-1 text-xs font-semibold uppercase tracking-wider bg-ink text-ivory rounded-sm hover:bg-sage transition-colors"
                >
                  Sign In
                </button>
              )}
            </div>

            {/* Health status */}
            <div className="hidden lg:flex items-center pl-2 border-l border-parchment-deep">
              {health ? (
                <span
                  className="inline-flex items-center text-xs text-sage"
                  title={`API: ${health.status} | DB: ${health.database} | AI: ${health.ai}`}
                >
                  <span className="h-2 w-2 rounded-full bg-sage mr-1.5" />
                  System Online
                </span>
              ) : (
                <span className="inline-flex items-center text-xs text-ochre">
                  <span className="h-2 w-2 rounded-full bg-ochre mr-1.5" />
                  Connecting
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
      <BrandModal isOpen={isBrandModalOpen} onClose={() => setIsBrandModalOpen(false)} />
      <TeamModal isOpen={isTeamModalOpen} onClose={() => setIsTeamModalOpen(false)} />
    </>
  )
}
