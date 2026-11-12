/**
 * Dedicated Authentication Page inspired by Pod.ai's split-screen architecture.
 * Features:
 * - Brand identity and assurance panel (left).
 * - Multi-method authentication panel (right):
 *   1. Organisation / Workspace code lookup (backend-verified, privacy-safe).
 *   2. Direct email/password login.
 *   3. New organisation registration.
 *   4. One-click role-based Demo Login (Brand Manager, Creator, Auditor).
 *   5. Automatic post-login brand routing.
 */

import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { OrganisationLookupResponse } from '../api/types'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, token, isLoading, login, register, demoLogin } = useAuth()

  // Automatically route authenticated users to workspace or intended destination
  useEffect(() => {
    if (!isLoading && user && token) {
      const from = (location.state as { from?: string } | undefined)?.from || '/workspace'
      navigate(from, { replace: true })
    }
  }, [user, token, isLoading, navigate, location.state])

  // Mode: 'login' | 'register'
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')

  // Direct login state
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Registration state
  const [orgName, setOrgName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regError, setRegError] = useState<string | null>(null)

  // Organisation lookup state
  const [lookupQuery, setLookupQuery] = useState('')
  const [lookupResult, setLookupResult] = useState<OrganisationLookupResponse | null>(null)
  const [isLookingUp, setIsLookingUp] = useState(false)
  const [lookupAttempted, setLookupAttempted] = useState(false)

  // Handle post-login brand navigation
  const handleRoutingOutcome = (status: 'single' | 'restored' | 'select_needed' | 'empty') => {
    if (status === 'single' || status === 'restored') {
      navigate('/workspace')
    } else {
      navigate('/select-brand')
    }
  }

  // Organisation lookup handler
  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!lookupQuery.trim() || lookupQuery.trim().length < 2) return

    setIsLookingUp(true)
    setLookupAttempted(true)
    try {
      const res = await api.lookupOrganisation(lookupQuery.trim())
      setLookupResult(res)
    } catch {
      setLookupResult({
        exists: false,
        name: null,
        slug: null,
        message: 'Could not connect to organisation directory.',
      })
    } finally {
      setIsLookingUp(false)
    }
  }

  // Direct login handler
  const handleDirectLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoginError(null)
    setIsSubmitting(true)

    try {
      const routing = await login({ email: email.trim(), password })
      handleRoutingOutcome(routing.status)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setLoginError(err.message)
      } else {
        setLoginError('Invalid email or password.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  // Registration handler
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setRegError(null)
    setIsSubmitting(true)

    try {
      const routing = await register({
        organisation_name: orgName.trim(),
        display_name: displayName.trim(),
        email: regEmail.trim(),
        password: regPassword,
      })
      handleRoutingOutcome(routing.status)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setRegError(err.message)
      } else {
        setRegError('Registration failed. Please check your inputs.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  // Demo login handler
  const handleDemoClick = async (role: 'admin' | 'creator' | 'reviewer') => {
    setLoginError(null)
    setIsSubmitting(true)
    try {
      const routing = await demoLogin(role)
      handleRoutingOutcome(routing.status)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setLoginError(err.message)
      } else {
        setLoginError('Demo authentication failed.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-ivory">
      {/* LEFT PANEL — Brand Identity & Assurances (Inspired by Pod.ai) */}
      <div className="md:w-5/12 bg-plum text-ivory p-8 sm:p-12 lg:p-16 flex flex-col justify-between relative overflow-hidden">
        {/* Subtle geometric background accents */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-plum-soft rounded-full -translate-y-1/2 translate-x-1/2 opacity-30 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-rose/10 rounded-full translate-y-1/3 -translate-x-1/3 pointer-events-none" />

        {/* Top Header */}
        <div className="relative z-10 space-y-6">
          <Link to="/" className="inline-flex items-baseline space-x-2 group">
            <span className="font-serif text-3xl font-bold tracking-tight text-ivory group-hover:text-rose transition-colors">
              Inkloom AI
            </span>
            <span className="text-[11px] uppercase tracking-widest text-sage-muted font-medium">
              Enterprise
            </span>
          </Link>

          <div className="space-y-4 pt-10">
            <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight text-ivory">
              Autonomous Brand Governance for High-Velocity Teams.
            </h1>
            <p className="text-sm sm:text-base text-ivory/80 leading-relaxed max-w-md">
              Ensuring every brand campaign, promotional document, and visual asset is authentic, compliant, and rigorously grounded.
            </p>
          </div>
        </div>

        {/* Key Features List */}
        <div className="relative z-10 my-10 space-y-4">
          <div className="flex items-start space-x-3 p-3 bg-plum-soft/60 rounded-sm border border-ivory/10">
            <span className="text-terracotta text-base">✦</span>
            <div>
              <div className="text-xs font-semibold text-ivory">Multi-Brand Tenant Isolation</div>
              <div className="text-[11px] text-ivory/70">
                Independent guidelines, facts, and terminology with role-based access.
              </div>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-3 bg-plum-soft/60 rounded-sm border border-ivory/10">
            <span className="text-sage-muted text-base">✦</span>
            <div>
              <div className="text-xs font-semibold text-ivory">Multimodal Document OCR & Logo Match</div>
              <div className="text-[11px] text-ivory/70">
                Extract text from promotional images, scanned PDFs, and verify approved logos.
              </div>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-3 bg-plum-soft/60 rounded-sm border border-ivory/10">
            <span className="text-rose text-base">✦</span>
            <div>
              <div className="text-xs font-semibold text-ivory">Grounded Claim-Level Verification</div>
              <div className="text-[11px] text-ivory/70">
                Deterministic rule enforcement paired with Gemini semantic grounding.
              </div>
            </div>
          </div>
        </div>

        {/* Left Footer */}
        <div className="relative z-10 pt-6 border-t border-ivory/10 text-xs text-ivory/60 flex items-center justify-between">
          <span>Inkloom AI v1.0.0</span>
          <span>Security & Grounding Certified</span>
        </div>
      </div>

      {/* RIGHT PANEL — Authentication & Organisation Routing */}
      <div className="md:w-7/12 p-8 sm:p-12 lg:p-16 flex flex-col justify-center bg-ivory">
        <div className="max-w-xl w-full mx-auto space-y-8">
          {/* Welcome Headline */}
          <div className="space-y-2">
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-ink">
              {authMode === 'login' ? 'Welcome to Inkloom!' : 'Register Your Organisation'}
            </h2>
            <p className="text-sm text-ink-soft">
              {authMode === 'login'
                ? 'Verify your organisation or log in directly with your account credentials.'
                : 'Create an isolated organisation tenant and configure your initial Brand Manager.'}
            </p>
          </div>

          {authMode === 'login' ? (
            <>
              {/* 1. Organisation Lookup Box (Inspired by Pod.ai search box) */}
              <div className="bg-plum-light/50 border border-plum/15 rounded-sm p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="org-search"
                    className="block text-xs font-semibold text-plum uppercase tracking-wider"
                  >
                    Search for your organisation or workspace code
                  </label>
                  {lookupResult?.exists && (
                    <span className="text-[11px] text-sage font-semibold flex items-center">
                      <span className="h-1.5 w-1.5 rounded-full bg-sage mr-1" />
                      Verified
                    </span>
                  )}
                </div>

                <form onSubmit={handleLookup} className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      id="org-search"
                      type="text"
                      value={lookupQuery}
                      onChange={(e) => {
                        setLookupQuery(e.target.value)
                        setLookupAttempted(false)
                      }}
                      placeholder="e.g. lumacare-global or LumaCare"
                      className="w-full px-3.5 py-2 text-xs text-ink bg-ivory rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isLookingUp || lookupQuery.trim().length < 2}
                    className="px-4 py-2 bg-plum text-ivory text-xs font-semibold rounded-sm hover:bg-plum-soft disabled:opacity-50 transition-colors shrink-0"
                  >
                    {isLookingUp ? 'Searching...' : 'Lookup'}
                  </button>
                </form>

                {/* Lookup Feedback */}
                {lookupAttempted && lookupResult && (
                  <div
                    className={`text-xs p-2.5 rounded-sm border ${
                      lookupResult.exists
                        ? 'bg-sage-light text-sage border-sage/30'
                        : 'bg-terracotta-soft/50 text-terracotta-dark border-terracotta/30'
                    }`}
                  >
                    {lookupResult.exists ? (
                      <div className="flex items-center justify-between">
                        <span>
                          <strong>{lookupResult.name}</strong> (workspace:{' '}
                          <code className="bg-sage/10 px-1 py-0.5 rounded">{lookupResult.slug}</code>)
                        </span>
                        <span className="text-[11px] font-medium">Proceed below to log in ↓</span>
                      </div>
                    ) : (
                      <span>{lookupResult.message || 'No organisation found with this name.'}</span>
                    )}
                  </div>
                )}
                <p className="text-[11px] text-ink-soft/80">
                  Lookup verifies workspace eligibility securely without exposing member credentials or private tenant data.
                </p>
              </div>

              {/* OR Divider */}
              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-parchment-deep" />
                <span className="flex-shrink mx-4 text-xs font-semibold tracking-wider text-ink-soft/70 uppercase">
                  OR
                </span>
                <div className="flex-grow border-t border-parchment-deep" />
              </div>

              {/* 2. Direct Email/Password Login Form */}
              <form onSubmit={handleDirectLogin} className="space-y-4">
                <div className="text-xs font-semibold text-ink uppercase tracking-wider">
                  Log in directly using your account credentials
                </div>

                {loginError && (
                  <div className="p-3 bg-terracotta-soft text-terracotta-dark text-xs rounded-sm border border-terracotta/30">
                    {loginError}
                  </div>
                )}

                <div className="space-y-1">
                  <label htmlFor="login-email" className="block text-xs font-medium text-ink-soft">
                    Email Address*
                  </label>
                  <input
                    id="login-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@organisation.com"
                    className="w-full px-3.5 py-2 text-xs text-ink bg-parchment/40 rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label htmlFor="login-password" className="block text-xs font-medium text-ink-soft">
                      Password*
                    </label>
                  </div>
                  <input
                    id="login-password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full px-3.5 py-2 text-xs text-ink bg-parchment/40 rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 bg-terracotta text-ivory text-xs font-semibold rounded-sm hover:bg-terracotta-dark transition-colors shadow-sm disabled:opacity-50"
                >
                  {isSubmitting ? 'Authenticating...' : 'Log In'}
                </button>
              </form>

              {/* 3. Register Organisation Toggle */}
              <div className="pt-2 text-center text-xs text-ink-soft">
                <span>Need a brand workspace for your enterprise? </span>
                <button
                  type="button"
                  onClick={() => setAuthMode('register')}
                  className="font-semibold text-plum hover:underline ml-1"
                >
                  Register new organisation →
                </button>
              </div>

              {/* 4. One-Click Role-Based Demo Login */}
              <div className="pt-6 border-t border-parchment-deep space-y-3">
                <div className="text-xs font-semibold text-ink uppercase tracking-wider flex items-center justify-between">
                  <span>Explore with live demo roles</span>
                  <span className="text-[10px] text-sage font-medium">LumaCare Demo Workspace</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => handleDemoClick('admin')}
                    disabled={isSubmitting}
                    className="px-3 py-2 text-left bg-parchment hover:bg-parchment-deep/70 rounded-sm border border-parchment-deep text-ink transition-colors group"
                  >
                    <div className="text-xs font-bold text-plum group-hover:text-terracotta">
                      Brand Manager
                    </div>
                    <div className="text-[10px] text-ink-soft">Full governance admin</div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleDemoClick('creator')}
                    disabled={isSubmitting}
                    className="px-3 py-2 text-left bg-parchment hover:bg-parchment-deep/70 rounded-sm border border-parchment-deep text-ink transition-colors group"
                  >
                    <div className="text-xs font-bold text-plum group-hover:text-terracotta">
                      Content Creator
                    </div>
                    <div className="text-[10px] text-ink-soft">Author & submit copy</div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleDemoClick('reviewer')}
                    disabled={isSubmitting}
                    className="px-3 py-2 text-left bg-parchment hover:bg-parchment-deep/70 rounded-sm border border-parchment-deep text-ink transition-colors group"
                  >
                    <div className="text-xs font-bold text-plum group-hover:text-terracotta">
                      Compliance Auditor
                    </div>
                    <div className="text-[10px] text-ink-soft">Audit & review runs</div>
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* REGISTRATION FORM */
            <form onSubmit={handleRegister} className="space-y-4">
              {regError && (
                <div className="p-3 bg-terracotta-soft text-terracotta-dark text-xs rounded-sm border border-terracotta/30">
                  {regError}
                </div>
              )}

              <div className="space-y-1">
                <label htmlFor="reg-org" className="block text-xs font-medium text-ink-soft">
                  Organisation Name*
                </label>
                <input
                  id="reg-org"
                  type="text"
                  required
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="e.g. Acme Health Labs"
                  className="w-full px-3.5 py-2 text-xs text-ink bg-parchment/40 rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="reg-name" className="block text-xs font-medium text-ink-soft">
                  Your Full Name*
                </label>
                <input
                  id="reg-name"
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Sarah Connor"
                  className="w-full px-3.5 py-2 text-xs text-ink bg-parchment/40 rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="reg-email" className="block text-xs font-medium text-ink-soft">
                  Business Email*
                </label>
                <input
                  id="reg-email"
                  type="email"
                  required
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="sarah@acme.com"
                  className="w-full px-3.5 py-2 text-xs text-ink bg-parchment/40 rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="reg-password" className="block text-xs font-medium text-ink-soft">
                  Password* (minimum 8 characters)
                </label>
                <input
                  id="reg-password"
                  type="password"
                  required
                  minLength={8}
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2 text-xs text-ink bg-parchment/40 rounded-sm border border-parchment-deep focus:outline-none focus:border-plum"
                />
              </div>

              <p className="text-[11px] text-ink-soft">
                As the founding registrant, you will be assigned the <strong>Brand Manager</strong> role with authority to create and administer brand workspaces.
              </p>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 bg-plum text-ivory text-xs font-semibold rounded-sm hover:bg-plum-soft transition-colors shadow-sm disabled:opacity-50"
              >
                {isSubmitting ? 'Registering...' : 'Register Organisation & Launch'}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => setAuthMode('login')}
                  className="text-xs font-medium text-ink-soft hover:text-plum"
                >
                  ← Back to Direct Login
                </button>
              </div>
            </form>
          )}

          {/* Footer links */}
          <div className="pt-8 border-t border-parchment-deep flex items-center justify-between text-xs text-ink-soft">
            <Link to="/" className="hover:text-plum">
              ← Return to Homepage
            </Link>
            <div className="flex space-x-4">
              <Link to="/terms" className="hover:text-plum">
                Terms of Use
              </Link>
              <Link to="/privacy" className="hover:text-plum">
                Privacy Policy
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
