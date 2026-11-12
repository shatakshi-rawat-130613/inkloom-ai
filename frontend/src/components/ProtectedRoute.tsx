/**
 * Route protection wrapper for Inkloom AI workspace and submission workflows.
 *
 * Ensures:
 * 1. Protected page content is never rendered while authentication state is loading/restoring.
 * 2. Unauthenticated or expired sessions are immediately redirected to /login using history replacement.
 * 3. Browser Back/Forward navigation cannot restore protected content after logout.
 */

import { type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, token, isLoading } = useAuth()
  const location = useLocation()

  // 1. Never render protected content while session is being verified/restored
  if (isLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <div className="h-8 w-8 rounded-full border-2 border-sage border-t-transparent animate-spin" />
        <p className="text-xs font-serif text-ink-soft">Verifying authentication session...</p>
      </div>
    )
  }

  // 2. Redirect to /login with history replacement if no valid authenticated session
  if (!user || !token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  // 3. Render protected content only when authenticated
  return <>{children}</>
}
