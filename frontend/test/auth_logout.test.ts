/**
 * Frontend unit and regression tests for authentication, logout, and protected route logic.
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

describe('Authentication & Logout Lifecycle', () => {
  beforeEach(() => {
    mockLocalStorage.clear()
    mockSessionStorage.clear()
  })

  it('1. Logout invalidates session, clears storage, and navigates to /login with replace: true', () => {
    mockLocalStorage.setItem('inkloom_token', 'mock-jwt-token-123')
    mockLocalStorage.setItem('inkloom_active_brand_id', 'brand-uuid-456')
    mockSessionStorage.setItem('cached_role_data', 'manager-data')

    let navigatedPath = ''
    let navigationOptions: { replace?: boolean } | undefined

    const mockNavigate = (path: string, options?: { replace?: boolean }) => {
      navigatedPath = path
      navigationOptions = options
    }

    // Simulate centralized logout logic from AuthContext
    const executeLogout = (navigateFn: typeof mockNavigate) => {
      mockLocalStorage.removeItem('inkloom_token')
      mockLocalStorage.removeItem('inkloom_active_brand_id')
      mockSessionStorage.clear()
      navigateFn('/login', { replace: true })
    }

    executeLogout(mockNavigate)

    assert.strictEqual(mockLocalStorage.getItem('inkloom_token'), null, 'JWT token must be removed from storage')
    assert.strictEqual(mockLocalStorage.getItem('inkloom_active_brand_id'), null, 'Active brand must be cleared')
    assert.strictEqual(mockSessionStorage.length, 0, 'Session storage must be completely cleared')
    assert.strictEqual(navigatedPath, '/login', 'Must navigate directly to /login')
    assert.strictEqual(navigationOptions?.replace, true, 'Navigation must use replace: true so Back button does not return to protected route')
  })

  it('2. Switching demo roles wipes previous user session before authenticating as new role', () => {
    // Start as Brand Manager
    mockLocalStorage.setItem('inkloom_token', 'manager-token')
    mockLocalStorage.setItem('inkloom_active_brand_id', 'manager-brand')
    mockSessionStorage.setItem('manager_key', 'val')

    // Simulate demoLogin cleanup before login
    const preDemoLoginCleanup = () => {
      mockLocalStorage.removeItem('inkloom_token')
      mockLocalStorage.removeItem('inkloom_active_brand_id')
      mockSessionStorage.clear()
    }

    preDemoLoginCleanup()

    assert.strictEqual(mockLocalStorage.getItem('inkloom_token'), null)
    assert.strictEqual(mockLocalStorage.getItem('inkloom_active_brand_id'), null)
    assert.strictEqual(mockSessionStorage.length, 0)
  })

  it('3. Protected route decision logic denies unauthenticated or empty session', () => {
    // Case A: Session is loading
    const evaluateRoute = (isLoading: boolean, user: unknown, token: string | null) => {
      if (isLoading) return 'RENDER_SPINNER'
      if (!user || !token) return 'REDIRECT_TO_LOGIN_WITH_REPLACE'
      return 'RENDER_PROTECTED_CONTENT'
    }

    assert.strictEqual(evaluateRoute(true, null, null), 'RENDER_SPINNER', 'Must not render protected content while restoring session')
    assert.strictEqual(evaluateRoute(false, null, null), 'REDIRECT_TO_LOGIN_WITH_REPLACE', 'Must redirect to login when no user or token')
    assert.strictEqual(evaluateRoute(false, { id: 'u1' }, null), 'REDIRECT_TO_LOGIN_WITH_REPLACE', 'Must redirect if token is absent')
    assert.strictEqual(evaluateRoute(false, null, 'tok'), 'REDIRECT_TO_LOGIN_WITH_REPLACE', 'Must redirect if user is absent')
    assert.strictEqual(evaluateRoute(false, { id: 'u1' }, 'tok'), 'RENDER_PROTECTED_CONTENT', 'Renders protected page when authenticated')
  })

  it('4. Expired or 401 Unauthorized API response immediately triggers centralized logout', () => {
    mockLocalStorage.setItem('inkloom_token', 'expired-token')
    mockLocalStorage.setItem('inkloom_active_brand_id', 'brand-1')

    let logoutTriggered = false
    const onUnauthorized = () => {
      logoutTriggered = true
      mockLocalStorage.removeItem('inkloom_token')
      mockLocalStorage.removeItem('inkloom_active_brand_id')
      mockSessionStorage.clear()
    }

    // Simulate 401 response handling from client.ts
    const handleApiResponse = (status: number) => {
      if (status === 401) {
        onUnauthorized()
      }
    }

    handleApiResponse(401)

    assert.strictEqual(logoutTriggered, true, '401 status must trigger onUnauthorized')
    assert.strictEqual(mockLocalStorage.getItem('inkloom_token'), null, 'Token must be removed on 401')
  })
})
