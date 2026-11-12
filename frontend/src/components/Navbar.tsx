/**
 * Application Navigation Bar.
 * Clean, editorial, typography-driven header with:
 * - Public navigation for landing page (Home, Platform, Solutions, How It Works, About, Login, Demo Login).
 * - Application workspace controls (Active brand indicator, brand switcher, team management, role pill, sign out).
 * - Service health indicator.
 */

import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { HealthResponse } from '../api/types'
import { useAuth } from '../context/AuthContext'
import { BrandModal } from './BrandModal'
import { TeamModal } from './TeamModal'

export function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [isBrandModalOpen, setIsBrandModalOpen] = useState(false)
  const [isTeamModalOpen, setIsTeamModalOpen] = useState(false)
  const [isDemoMenuOpen, setIsDemoMenuOpen] = useState(false)
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false)

  const { user, logout, activeBrand, availableBrands, switchBrand, demoLogin } = useAuth()

  const isPublicPage =
    location.pathname === '/' ||
    location.pathname === '/login' ||
    location.pathname === '/select-brand' ||
    location.pathname === '/terms' ||
    location.pathname === '/privacy'

  // Route-aware navigation handler for hash sections and home
  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, targetHash: string) => {
    e.preventDefault()
    setIsMobileNavOpen(false)

    if (location.pathname === '/') {
      if (!targetHash || targetHash === '#home') {
        window.scrollTo({ top: 0, behavior: 'smooth' })
        if (location.hash) {
          navigate('/', { replace: false })
        }
      } else {
        const id = targetHash.replace('#', '')
        const el = document.getElementById(id)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth' })
          navigate(`/${targetHash}`, { replace: false })
        }
      }
    } else {
      // Coming from another route (/login, /select-brand, etc.)
      if (!targetHash || targetHash === '#home') {
        navigate('/')
      } else {
        navigate(`/${targetHash}`)
      }
    }
  }

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

  const handleDemoLaunch = async (role: 'admin' | 'creator' | 'reviewer') => {
    setIsDemoMenuOpen(false)
    try {
      const res = await demoLogin(role)
      if (res.status === 'single' || res.status === 'restored') {
        navigate('/workspace')
      } else {
        navigate('/select-brand')
      }
    } catch {
      navigate('/login')
    }
  }

  return (
    <>
      <header className="border-b border-parchment-deep bg-ivory/95 sticky top-0 z-30 backdrop-blur-sm">
        <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
          {/* Left: Brand Identity & Active Workspace Context */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            <Link
              to="/"
              onClick={(e) => handleNavClick(e, '')}
              className="flex items-baseline space-x-2 group"
            >
              <span className="font-serif text-2xl font-bold tracking-tight text-ink group-hover:text-plum transition-colors">
                Inkloom AI
              </span>
              <span className="text-xs uppercase tracking-widest text-sage font-semibold">
                Brand Governance
              </span>
            </Link>

            {/* In-App Active Brand Badge / Switcher (when authenticated or in workspace) */}
            {user && (
              <>
                <span className="hidden sm:inline-block h-4 w-px bg-parchment-deep" />
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
                        className="px-2.5 py-1 text-xs text-ink font-semibold bg-parchment rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                      >
                        {availableBrands.map((b) => (
                          <option key={b.id} value={b.id}>
                            {b.name} {b.is_demo ? '(Demo)' : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : activeBrand ? (
                    <span className="inline-flex items-center px-2.5 py-1 text-xs font-semibold text-ink bg-parchment rounded-sm border border-parchment-deep">
                      <span className="h-1.5 w-1.5 rounded-full bg-sage mr-1.5" />
                      {activeBrand.name}
                    </span>
                  ) : (
                    <Link
                      to="/select-brand"
                      className="inline-flex items-center px-2 py-0.5 text-xs text-terracotta bg-terracotta-soft rounded-sm border border-terracotta/30"
                    >
                      Select Brand
                    </Link>
                  )}

                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() => setIsBrandModalOpen(true)}
                      title="Create new brand in your organisation"
                      className="px-2 py-1 text-[11px] font-semibold text-plum bg-plum-light border border-plum/20 rounded-sm hover:bg-plum hover:text-ivory transition-colors"
                    >
                      + Brand
                    </button>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Right Navigation & Controls */}
          <div className="flex items-center space-x-3 sm:space-x-5">
            {/* Public Landing & Marketing Navigation Links */}
            {isPublicPage ? (
              <nav className="hidden md:flex items-center space-x-5 text-xs font-medium text-ink-soft">
                <Link
                  to="/"
                  onClick={(e) => handleNavClick(e, '')}
                  className="hover:text-plum transition-colors"
                >
                  Home
                </Link>
                <Link
                  to="/#platform"
                  onClick={(e) => handleNavClick(e, '#platform')}
                  className="hover:text-plum transition-colors"
                >
                  Platform
                </Link>
                <Link
                  to="/#solutions"
                  onClick={(e) => handleNavClick(e, '#solutions')}
                  className="hover:text-plum transition-colors"
                >
                  Solutions
                </Link>
                <Link
                  to="/#how-it-works"
                  onClick={(e) => handleNavClick(e, '#how-it-works')}
                  className="hover:text-plum transition-colors"
                >
                  How It Works
                </Link>
                <Link
                  to="/#about"
                  onClick={(e) => handleNavClick(e, '#about')}
                  className="hover:text-plum transition-colors"
                >
                  About
                </Link>
              </nav>
            ) : (
              /* In-App Workspace Navigation Links */
              <nav className="flex items-center space-x-1 sm:space-x-3 text-xs sm:text-sm font-medium">
                <Link
                  to="/workspace"
                  className={`px-2.5 py-1 rounded-sm transition-colors ${
                    location.pathname === '/workspace'
                      ? 'text-ink bg-parchment border border-parchment-deep'
                      : 'text-ink-soft hover:text-ink hover:bg-parchment/60'
                  }`}
                >
                  Workspace
                </Link>
                <Link
                  to="/submissions/new"
                  className={`px-2.5 py-1 rounded-sm transition-colors ${
                    location.pathname === '/submissions/new'
                      ? 'text-ink bg-parchment border border-parchment-deep'
                      : 'text-ink-soft hover:text-ink hover:bg-parchment/60'
                  }`}
                >
                  Submit Content
                </Link>
              </nav>
            )}

            {/* Auth, Demo & User Session Controls */}
            <div className="flex items-center pl-2 sm:pl-3 border-l border-parchment-deep space-x-2">
              {user ? (
                <div className="flex items-center space-x-2">
                  {isPublicPage && (
                    <Link
                      to="/workspace"
                      className="hidden sm:inline-flex px-2.5 py-1 text-xs font-semibold text-ink bg-parchment border border-parchment-deep rounded-sm hover:border-plum transition-colors"
                    >
                      Workspace →
                    </Link>
                  )}

                  {isAdmin && !isPublicPage && (
                    <button
                      type="button"
                      onClick={() => setIsTeamModalOpen(true)}
                      className="px-2.5 py-1 text-xs font-semibold text-ink bg-parchment border border-parchment-deep rounded-sm hover:border-plum transition-colors"
                    >
                      Team
                    </button>
                  )}

                  <div className="text-right hidden sm:block">
                    <div className="text-xs font-semibold text-ink leading-tight">
                      {user.display_name}
                    </div>
                    <div className="text-[10px] text-sage font-medium uppercase tracking-wider">
                      {getRoleLabel(user.role)}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={logout}
                    className="px-2.5 py-1 text-xs font-medium text-ink-soft bg-parchment border border-parchment-deep rounded-sm hover:text-terracotta hover:border-terracotta/40 transition-colors"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                /* Unauthenticated Actions (Login & Demo Login) */
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsDemoMenuOpen(!isDemoMenuOpen)}
                      className="px-3 py-1.5 text-xs font-semibold text-plum bg-plum-light border border-plum/20 rounded-sm hover:bg-plum hover:text-ivory transition-colors"
                    >
                      Demo Login ▾
                    </button>

                    {isDemoMenuOpen && (
                      <div className="absolute right-0 mt-1 w-48 bg-ivory rounded-sm border border-parchment-deep shadow-lg py-1 z-40 text-xs">
                        <div className="px-3 py-1 text-[10px] uppercase font-bold text-ink-soft/70 border-b border-parchment-deep">
                          Select Demo Role
                        </div>
                        <button
                          type="button"
                          onClick={() => handleDemoLaunch('admin')}
                          className="w-full text-left px-3 py-2 hover:bg-parchment text-ink font-medium"
                        >
                          <div className="font-bold text-plum">Brand Manager</div>
                          <div className="text-[10px] text-ink-soft">Admin governance role</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDemoLaunch('creator')}
                          className="w-full text-left px-3 py-2 hover:bg-parchment text-ink font-medium"
                        >
                          <div className="font-bold text-plum">Content Creator</div>
                          <div className="text-[10px] text-ink-soft">Author submissions</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDemoLaunch('reviewer')}
                          className="w-full text-left px-3 py-2 hover:bg-parchment text-ink font-medium"
                        >
                          <div className="font-bold text-plum">Compliance Auditor</div>
                          <div className="text-[10px] text-ink-soft">Review & approve runs</div>
                        </button>
                      </div>
                    )}
                  </div>

                  <Link
                    to="/login"
                    className="px-3.5 py-1.5 text-xs font-semibold bg-terracotta text-ivory rounded-sm hover:bg-terracotta-dark transition-colors shadow-sm"
                  >
                    Login
                  </Link>
                </div>
              )}

              {/* Mobile menu toggle for public navigation */}
              {isPublicPage && (
                <button
                  type="button"
                  onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
                  className="md:hidden p-1.5 text-ink-soft hover:text-plum focus:outline-none ml-1"
                  aria-label="Toggle navigation menu"
                  aria-expanded={isMobileNavOpen}
                >
                  {isMobileNavOpen ? (
                    <span className="text-base font-bold leading-none">✕</span>
                  ) : (
                    <span className="text-base font-bold leading-none">☰</span>
                  )}
                </button>
              )}
            </div>

            {/* System Online / Health Status */}
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

        {/* Mobile Navigation Drawer */}
        {isMobileNavOpen && isPublicPage && (
          <div className="md:hidden border-t border-parchment-deep bg-ivory/98 px-6 py-4 space-y-3 text-xs font-medium shadow-md">
            <Link
              to="/"
              onClick={(e) => handleNavClick(e, '')}
              className="block py-1.5 text-ink hover:text-plum transition-colors"
            >
              Home
            </Link>
            <Link
              to="/#platform"
              onClick={(e) => handleNavClick(e, '#platform')}
              className="block py-1.5 text-ink hover:text-plum transition-colors"
            >
              Platform
            </Link>
            <Link
              to="/#solutions"
              onClick={(e) => handleNavClick(e, '#solutions')}
              className="block py-1.5 text-ink hover:text-plum transition-colors"
            >
              Solutions
            </Link>
            <Link
              to="/#how-it-works"
              onClick={(e) => handleNavClick(e, '#how-it-works')}
              className="block py-1.5 text-ink hover:text-plum transition-colors"
            >
              How It Works
            </Link>
            <Link
              to="/#about"
              onClick={(e) => handleNavClick(e, '#about')}
              className="block py-1.5 text-ink hover:text-plum transition-colors"
            >
              About
            </Link>
            {!user && (
              <div className="pt-3 border-t border-parchment-deep flex items-center space-x-3">
                <Link
                  to="/login"
                  onClick={() => setIsMobileNavOpen(false)}
                  className="px-3.5 py-1.5 bg-terracotta text-ivory text-xs font-semibold rounded-sm hover:bg-terracotta-dark transition-colors shadow-sm"
                >
                  Login
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    setIsMobileNavOpen(false)
                    handleDemoLaunch('reviewer')
                  }}
                  className="px-3 py-1.5 text-xs font-semibold text-plum bg-plum-light border border-plum/20 rounded-sm hover:bg-plum hover:text-ivory transition-colors"
                >
                  Try Demo
                </button>
              </div>
            )}
          </div>
        )}
      </header>

      <BrandModal isOpen={isBrandModalOpen} onClose={() => setIsBrandModalOpen(false)} />
      <TeamModal isOpen={isTeamModalOpen} onClose={() => setIsTeamModalOpen(false)} />
    </>
  )
}
