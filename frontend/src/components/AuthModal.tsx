/**
 * Authentication Modal for Login, Registration, and Quick Demo Role Selection.
 * Strict typography, warm editorial aesthetic adhering to Inkloom design system.
 */

import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const { login, register } = useAuth()
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [orgName, setOrgName] = useState('')

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      if (isRegister) {
        if (!orgName.trim() || !displayName.trim()) {
          setError('Please provide organisation name and display name.')
          setIsSubmitting(false)
          return
        }
        await register({
          organisation_name: orgName,
          display_name: displayName,
          email,
          password,
        })
      } else {
        await login({ email, password })
      }
      onClose()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Authentication request failed. Please check your credentials.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleQuickLogin = async (quickEmail: string) => {
    setError(null)
    setIsSubmitting(true)
    try {
      await login({ email: quickEmail, password: 'LumaCareDemo2026!' })
      onClose()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Demo authentication failed.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-md bg-ivory border border-parchment-deep rounded-sm shadow-xl overflow-hidden animate-fadeIn">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-parchment-deep flex items-baseline justify-between">
          <div>
            <h2 className="font-serif text-xl font-bold text-ink">
              {isRegister ? 'Register Organisation' : 'Account Sign In'}
            </h2>
            <p className="text-xs text-ink-soft mt-1">
              {isRegister
                ? 'Create a private multi-tenant brand governance workspace.'
                : 'Access your brand guidelines, submissions, and compliance runs.'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-ink-soft hover:text-ink text-sm px-2 py-1 rounded"
          >
            ✕
          </button>
        </div>

        {/* Tab Toggle */}
        <div className="flex border-b border-parchment-deep bg-parchment/40">
          <button
            type="button"
            onClick={() => {
              setIsRegister(false)
              setError(null)
            }}
            className={`flex-1 py-2.5 text-xs font-semibold tracking-wide uppercase transition-colors ${
              !isRegister
                ? 'text-ink border-b-2 border-sage bg-ivory'
                : 'text-ink-soft hover:text-ink'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsRegister(true)
              setError(null)
            }}
            className={`flex-1 py-2.5 text-xs font-semibold tracking-wide uppercase transition-colors ${
              isRegister
                ? 'text-ink border-b-2 border-sage bg-ivory'
                : 'text-ink-soft hover:text-ink'
            }`}
          >
            New Organisation
          </button>
        </div>

        {/* Quick Demo Identities (when in sign in mode) */}
        {!isRegister && (
          <div className="px-6 pt-4 pb-2 bg-parchment/20 border-b border-parchment-deep">
            <div className="text-[11px] font-semibold text-ink-soft uppercase tracking-wider mb-2">
              Instant Demo Access (LumaCare):
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@lumacare.demo')}
                disabled={isSubmitting}
                className="px-2 py-1.5 bg-ivory border border-parchment-deep rounded-sm text-left hover:border-sage transition-colors"
              >
                <div className="text-xs font-bold text-ink">Brand Mgr</div>
                <div className="text-[10px] text-sage">Admin role</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('editor@lumacare.demo')}
                disabled={isSubmitting}
                className="px-2 py-1.5 bg-ivory border border-parchment-deep rounded-sm text-left hover:border-sage transition-colors"
              >
                <div className="text-xs font-bold text-ink">Creator</div>
                <div className="text-[10px] text-ink-soft">Editor role</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('reviewer@lumacare.demo')}
                disabled={isSubmitting}
                className="px-2 py-1.5 bg-ivory border border-parchment-deep rounded-sm text-left hover:border-sage transition-colors"
              >
                <div className="text-xs font-bold text-ink">Auditor</div>
                <div className="text-[10px] text-ink-soft">Reviewer role</div>
              </button>
            </div>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-terracotta/10 border border-terracotta/30 text-terracotta text-xs rounded-sm">
              {error}
            </div>
          )}

          {isRegister && (
            <>
              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Organisation Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Health Products"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
                  Your Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Elena Vance"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink uppercase tracking-wider mb-1">
              Password
            </label>
            <input
              type="password"
              required
              minLength={8}
              placeholder="Minimum 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 bg-ink text-ivory text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-sage transition-colors disabled:opacity-50"
            >
              {isSubmitting
                ? 'Processing...'
                : isRegister
                ? 'Create Organisation & Workspace'
                : 'Sign In'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
