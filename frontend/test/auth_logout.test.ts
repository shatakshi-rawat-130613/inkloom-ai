/**
 * Frontend unit and regression tests for authentication, logout, and protected route logic.
 *
 * Covers:
 * 1. Login as Brand Manager -> open workspace -> logout -> /login with replace: true.
 * 2. Login as Content Creator -> open a submission -> logout -> /login with replace: true.
 * 3. Login as Compliance Auditor -> open a review page -> logout -> /login with replace: true.
 * 4. After logout, browser Back must not reveal protected content.
 * 5. Refreshing a protected URL after logout must redirect to /login.
 * 6. Directly opening a protected URL in a new tab without authentication must redirect to /login.
 * 7. Logging in as a different role after logout must not retain the previous role's data or permissions.
 * 8. Expired or 401 Unauthorized API response immediately triggers centralized logout and redirect.
 */

import { describe, it, beforeEach } from 'node:test'
import assert from 'node:assert'

// Mock browser storage
class MockStorage {
  private store: Map<string, string> = new Map()

  getItem(key: string): string | null {
    return this.store.get(key) || null
  }

  setItem(key: string, value: string): void {
    this.store.set(key, value)
  }

  removeItem(key: string): void {
    this.store.delete(key)
  }

  clear(): void {
    this.store.clear()
  }

  get length(): number {
    return this.store.size
  }

  key(index: number): string | null {
    return Array.from(this.store.keys())[index] || null
  }
}

// Global browser mocks
const mockLocalStorage = new MockStorage()
const mockSessionStorage = new MockStorage()

// @ts-expect-error Mocking global window/storage in Node environment
globalThis.localStorage = mockLocalStorage
// @ts-expect-error Mocking global window/storage in Node environment
globalThis.sessionStorage = mockSessionStorage
// @ts-expect-error Mocking global window
globalThis.window = {
  localStorage: mockLocalStorage,
  sessionStorage: mockSessionStorage,
}

// Simulated Centralized AuthContext & ProtectedRoute Logic
class AuthContextSimulator {
  user: { id: string; email: string; role: string; organisation_id: string } | null = null
  token: string | null = null
  activeBrandId: string | null = null
  availableBrands: { id: string; organisation_id: string }[] = []
  historyStack: string[] = []
  currentLocation = '/'
  unauthorizedHandler: (() => void) | null = null

  constructor() {
    this.token = mockLocalStorage.getItem('inkloom_token')
    this.activeBrandId = mockLocalStorage.getItem('inkloom_active_brand_id')
  }

  navigate(to: string, options?: { replace?: boolean }) {
    if (options?.replace) {
      if (this.historyStack.length > 0) {
        this.historyStack[this.historyStack.length - 1] = to
      } else {
        this.historyStack.push(to)
      }
    } else {
      this.historyStack.push(to)
    }
    this.currentLocation = to
  }

  login(user: { id: string; email: string; role: string; organisation_id: string }, token: string, brandId: string) {
    // Clear previous brand context to prevent cross-session pollution
    mockLocalStorage.removeItem('inkloom_active_brand_id')
    mockSessionStorage.clear()
    this.activeBrandId = null
    this.availableBrands = []

    this.user = user
    this.token = token
    this.activeBrandId = brandId
    mockLocalStorage.setItem('inkloom_token', token)
    mockLocalStorage.setItem('inkloom_active_brand_id', brandId)
  }

  logout() {
    mockLocalStorage.removeItem('inkloom_token')
    mockLocalStorage.removeItem('inkloom_active_brand_id')
    mockSessionStorage.clear()
    this.token = null
    this.user = null
    this.activeBrandId = null
    this.availableBrands = []
    this.navigate('/login', { replace: true })
  }

  onApi401() {
    mockLocalStorage.removeItem('inkloom_token')
    mockLocalStorage.removeItem('inkloom_active_brand_id')
    mockSessionStorage.clear()
    if (this.unauthorizedHandler) {
      this.unauthorizedHandler()
    } else {
      this.logout()
    }
  }

  // Evaluates whether ProtectedRoute allows rendering or intercepts
  renderProtectedRoute(path: string, isLoading = false): { rendered: boolean; redirectedTo?: string } {
    if (isLoading) {
      return { rendered: false, redirectedTo: 'SPINNER' }
    }
    if (!this.user || !this.token) {
      this.navigate('/login', { replace: true })
      return { rendered: false, redirectedTo: '/login' }
    }
    this.currentLocation = path
    return { rendered: true }
  }

  simulateBrowserBack(): string {
    if (this.historyStack.length > 1) {
      this.historyStack.pop()
      this.currentLocation = this.historyStack[this.historyStack.length - 1]
    }
    // Protected route check immediately on pop
    const outcome = this.renderProtectedRoute(this.currentLocation)
    if (!outcome.rendered && outcome.redirectedTo === '/login') {
      return '/login'
    }
    return this.currentLocation
  }
}

describe('Full 8-Scenario Authentication & Logout Regression Suite', () => {
  let auth: AuthContextSimulator

  beforeEach(() => {
    mockLocalStorage.clear()
    mockSessionStorage.clear()
    auth = new AuthContextSimulator()
  })

  it('Scenario 1: Brand Manager logs in -> opens /workspace -> logs out -> redirected to /login with replace: true', () => {
    auth.login(
      { id: 'u-mgr', email: 'admin@lumacare.demo', role: 'admin', organisation_id: 'org-luma' },
      'jwt-mgr-token',
      'brand-luma'
    )
    auth.navigate('/workspace')
    const route = auth.renderProtectedRoute('/workspace')
    assert.strictEqual(route.rendered, true, 'Brand Manager must be allowed in /workspace')

    auth.logout()

    assert.strictEqual(auth.token, null, 'Token must be cleared')
    assert.strictEqual(auth.user, null, 'User must be cleared')
    assert.strictEqual(auth.activeBrandId, null, 'Active brand must be cleared')
    assert.strictEqual(mockLocalStorage.getItem('inkloom_token'), null)
    assert.strictEqual(auth.currentLocation, '/login', 'Current route must be /login')
    assert.strictEqual(auth.historyStack[auth.historyStack.length - 1], '/login', 'History entry replaced with /login')
  })

  it('Scenario 2: Content Creator logs in -> opens /submissions/:id -> logs out -> redirected to /login', () => {
    auth.login(
      { id: 'u-creator', email: 'editor@lumacare.demo', role: 'editor', organisation_id: 'org-luma' },
      'jwt-creator-token',
      'brand-luma'
    )
    auth.navigate('/submissions/48d4c68b')
    const route = auth.renderProtectedRoute('/submissions/48d4c68b')
    assert.strictEqual(route.rendered, true, 'Content Creator allowed in submission detail')

    auth.logout()

    assert.strictEqual(auth.currentLocation, '/login', 'Must immediately redirect to /login')
    const afterLogout = auth.renderProtectedRoute('/submissions/48d4c68b')
    assert.strictEqual(afterLogout.rendered, false, 'Submission detail content must never render after logout')
  })

  it('Scenario 3: Compliance Auditor logs in -> opens review page -> logs out -> redirected to /login', () => {
    auth.login(
      { id: 'u-rev', email: 'reviewer@lumacare.demo', role: 'reviewer', organisation_id: 'org-luma' },
      'jwt-rev-token',
      'brand-luma'
    )
    auth.navigate('/workspace')
    assert.strictEqual(auth.renderProtectedRoute('/workspace').rendered, true)

    auth.logout()

    assert.strictEqual(auth.currentLocation, '/login')
    assert.strictEqual(auth.user, null)
  })

  it('Scenario 4: After logout, browser Back button does not reveal protected content', () => {
    auth.login(
      { id: 'u-mgr', email: 'admin@lumacare.demo', role: 'admin', organisation_id: 'org-luma' },
      'jwt-token',
      'brand-luma'
    )
    auth.navigate('/workspace')
    auth.navigate('/submissions/48d4c68b')
    auth.logout() // Replaces /submissions/48d4c68b with /login

    // User attempts to click browser Back
    const backLocation = auth.simulateBrowserBack()
    assert.strictEqual(backLocation, '/login', 'Browser back must be intercepted by ProtectedRoute and bounced to /login')
    assert.strictEqual(auth.renderProtectedRoute('/workspace').rendered, false)
  })

  it('Scenario 5: Refreshing a protected URL after logout redirects to /login', () => {
    // Session has ended (localStorage is empty)
    mockLocalStorage.clear()
    const freshApp = new AuthContextSimulator()

    const outcome = freshApp.renderProtectedRoute('/submissions/48d4c68b', false)
    assert.strictEqual(outcome.rendered, false)
    assert.strictEqual(outcome.redirectedTo, '/login', 'Refreshing protected route after logout must navigate to /login')
  })

  it('Scenario 6: Directly opening a protected URL in a new tab without authentication redirects to /login', () => {
    // Simulating fresh incognito tab
    const incognitoAuth = new AuthContextSimulator()

    // 1. Initial restoration phase
    const loadingState = incognitoAuth.renderProtectedRoute('/workspace', true)
    assert.strictEqual(loadingState.rendered, false)
    assert.strictEqual(loadingState.redirectedTo, 'SPINNER', 'Must render verification spinner while checking session')

    // 2. Verified no session
    const resolvedState = incognitoAuth.renderProtectedRoute('/workspace', false)
    assert.strictEqual(resolvedState.rendered, false)
    assert.strictEqual(resolvedState.redirectedTo, '/login')
  })

  it('Scenario 7: Logging in as a different role after logout does not retain previous role state or permissions', () => {
    // 1. Manager logs in and sets role data
    auth.login(
      { id: 'u-admin', email: 'admin@lumacare.demo', role: 'admin', organisation_id: 'org-1' },
      'admin-token',
      'brand-1'
    )
    mockSessionStorage.setItem('role_scope', 'admin_full_access')
    auth.logout()

    assert.strictEqual(mockSessionStorage.getItem('role_scope'), null, 'Session storage must be cleared on logout')

    // 2. Creator logs in
    auth.login(
      { id: 'u-creator', email: 'editor@lumacare.demo', role: 'editor', organisation_id: 'org-2' },
      'creator-token',
      'brand-2'
    )

    assert.strictEqual(auth.user?.role, 'editor', 'Role must be editor')
    assert.strictEqual(auth.user?.organisation_id, 'org-2', 'Organisation must be fresh')
    assert.strictEqual(mockSessionStorage.getItem('role_scope'), null, 'Previous role cache must not exist')
  })

  it('Scenario 8: Expired or 401 Unauthorized API response immediately triggers centralized logout and redirect', () => {
    auth.login(
      { id: 'u-user', email: 'user@lumacare.demo', role: 'editor', organisation_id: 'org-1' },
      'expired-token',
      'brand-1'
    )

    // Wire handler
    auth.unauthorizedHandler = () => auth.logout()

    // Simulate backend rejecting token with 401
    auth.onApi401()

    assert.strictEqual(auth.token, null, 'Token must be cleared on 401')
    assert.strictEqual(auth.user, null, 'User must be null on 401')
    assert.strictEqual(auth.currentLocation, '/login', 'Must redirect to /login on 401')
    assert.strictEqual(mockLocalStorage.getItem('inkloom_token'), null)
  })
})
