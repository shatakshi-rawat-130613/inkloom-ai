/**
 * Application Navigation Bar.
 * Clean, editorial, typography-driven header with service health indicator.
 */

import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import type { HealthResponse } from '../api/types'

export function Navbar() {
  const location = useLocation()
  const [health, setHealth] = useState<HealthResponse | null>(null)

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
    { to: '/', label: 'Demo Brand' },
    { to: '/submissions/new', label: 'Submit Content' },
    { to: '/terms', label: 'Terms' },
    { to: '/privacy', label: 'Privacy' },
  ]

  return (
    <header className="border-b border-parchment-deep bg-ivory/95 sticky top-0 z-20 backdrop-blur-none">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-6">
          <Link to="/" className="flex items-baseline space-x-2 group">
            <span className="font-serif text-2xl font-bold tracking-tight text-ink group-hover:text-sage transition-colors">
              Inkloom AI
            </span>
            <span className="text-xs uppercase tracking-widest text-sage font-medium">
              Brand Governance
            </span>
          </Link>

          <span className="hidden sm:inline-block h-4 w-px bg-parchment-deep" />

          <span className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs text-ink-soft bg-parchment rounded-sm border border-parchment-deep">
            Workspace: LumaCare Demo
          </span>
        </div>

        {/* Navigation links & health status */}
        <div className="flex items-center space-x-5">
          <nav className="flex items-center space-x-1 sm:space-x-4">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.to
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3 py-1.5 text-sm font-medium transition-colors rounded-sm ${
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

          <div className="hidden md:flex items-center pl-3 border-l border-parchment-deep">
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
  )
}
