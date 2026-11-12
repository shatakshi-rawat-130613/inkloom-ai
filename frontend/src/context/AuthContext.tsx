/**
 * Authentication and Multi-Tenant Brand Workspace Routing Context.
 * Manages user session, JWT persistence, organisation resolution,
 * authorised brand routing, and strict tenant isolation.
 */

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setUnauthorizedHandler } from '../api/client'
import type {
  BrandSummary,
  UserLoginRequest,
  UserRegisterRequest,
  UserResponse,
} from '../api/types'

export interface BrandRoutingResult {
  status: 'single' | 'restored' | 'select_needed' | 'empty'
  authorisedBrands: BrandSummary[]
  activeBrand: BrandSummary | null
}

interface AuthContextType {
  user: UserResponse | null
  token: string | null
  isLoading: boolean
  activeBrand: BrandSummary | null
  availableBrands: BrandSummary[]
  login: (payload: UserLoginRequest) => Promise<BrandRoutingResult>
  register: (payload: UserRegisterRequest) => Promise<BrandRoutingResult>
  demoLogin: (role: 'admin' | 'creator' | 'reviewer') => Promise<BrandRoutingResult>
  logout: () => void
  switchBrand: (brand: BrandSummary) => void
  selectBrandById: (brandId: string) => boolean
  refreshBrands: (currentUser?: UserResponse | null) => Promise<BrandRoutingResult>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'inkloom_token'
const ACTIVE_BRAND_KEY = 'inkloom_active_brand_id'

function filterAuthorisedBrands(
  brands: BrandSummary[],
  currentUser: UserResponse | null
): BrandSummary[] {
  if (!currentUser) {
    // Unauthenticated: only demo brand if public
    return brands.filter((b) => b.is_demo)
  }

  const isDemoUser =
    currentUser.email.toLowerCase().includes('lumacare.demo') ||
    currentUser.email.toLowerCase().includes('lumacare.internal') ||
    currentUser.organisation_name?.toLowerCase().includes('lumacare')

  return brands.filter((b) => {
    // Direct organisation ownership match
    if (b.organisation_id && currentUser.organisation_id) {
      if (b.organisation_id === currentUser.organisation_id) {
        return true
      }
    }
    // Demo user can access demo brand
    if (isDemoUser && b.is_demo) {
      return true
    }
    return false
  })
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [availableBrands, setAvailableBrands] = useState<BrandSummary[]>([])
  const [activeBrand, setActiveBrand] = useState<BrandSummary | null>(null)

  const resolveBrandState = (
    allBrands: BrandSummary[],
    currentUser: UserResponse | null
  ): BrandRoutingResult => {
    const authorised = filterAuthorisedBrands(allBrands, currentUser)
    setAvailableBrands(authorised)

    if (authorised.length === 0) {
      setActiveBrand(null)
      localStorage.removeItem(ACTIVE_BRAND_KEY)
      return { status: 'empty', authorisedBrands: [], activeBrand: null }
    }

    if (authorised.length === 1) {
      const single = authorised[0]
      setActiveBrand(single)
      localStorage.setItem(ACTIVE_BRAND_KEY, single.id)
      return { status: 'single', authorisedBrands: authorised, activeBrand: single }
    }

    // Multiple brands authorised: verify if saved brand is still valid
    const savedBrandId = localStorage.getItem(ACTIVE_BRAND_KEY)
    const validSaved = savedBrandId ? authorised.find((b) => b.id === savedBrandId) : null

    if (validSaved) {
      setActiveBrand(validSaved)
      return { status: 'restored', authorisedBrands: authorised, activeBrand: validSaved }
    }

    // Stale or no saved brand: require explicit user selection
    setActiveBrand(null)
    localStorage.removeItem(ACTIVE_BRAND_KEY)
    return { status: 'select_needed', authorisedBrands: authorised, activeBrand: null }
  }

  const refreshBrands = async (currentUser?: UserResponse | null): Promise<BrandRoutingResult> => {
    const targetUser = currentUser !== undefined ? currentUser : user
    try {
      const brands = await api.listBrands()
      return resolveBrandState(brands, targetUser)
    } catch {
      setAvailableBrands([])
      setActiveBrand(null)
      return { status: 'empty', authorisedBrands: [], activeBrand: null }
    }
  }

  // Initialize session on mount
  useEffect(() => {
    let mounted = true

    async function initAuth() {
      setIsLoading(true)
      const storedToken = localStorage.getItem(TOKEN_KEY)
      let resolvedUser: UserResponse | null = null

      if (storedToken) {
        try {
          const profile = await api.getMe()
          if (mounted) {
            setUser(profile)
            setToken(storedToken)
            resolvedUser = profile
          }
        } catch {
          if (mounted) {
            localStorage.removeItem(TOKEN_KEY)
            localStorage.removeItem(ACTIVE_BRAND_KEY)
            setToken(null)
            setUser(null)
            setActiveBrand(null)
            setAvailableBrands([])
          }
        }
      }

      try {
        const brands = await api.listBrands()
        if (mounted) {
          resolveBrandState(brands, resolvedUser)
        }
      } catch {
        if (mounted) {
          setAvailableBrands([])
          setActiveBrand(null)
        }
      }

      if (mounted) setIsLoading(false)
    }

    initAuth()

    return () => {
      mounted = false
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ACTIVE_BRAND_KEY)
    sessionStorage.clear()
    setToken(null)
    setUser(null)
    setActiveBrand(null)
    setAvailableBrands([])
    navigate('/login', { replace: true })
  }, [navigate])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout()
    })
    return () => {
      setUnauthorizedHandler(null)
    }
  }, [logout])

  const login = async (payload: UserLoginRequest): Promise<BrandRoutingResult> => {
    // Clear previous brand context to prevent cross-session context pollution
    localStorage.removeItem(ACTIVE_BRAND_KEY)
    sessionStorage.clear()
    setActiveBrand(null)
    setAvailableBrands([])

    const res = await api.login(payload)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    setToken(res.access_token)
    setUser(res.user)

    const allBrands = await api.listBrands()
    return resolveBrandState(allBrands, res.user)
  }

  const register = async (payload: UserRegisterRequest): Promise<BrandRoutingResult> => {
    localStorage.removeItem(ACTIVE_BRAND_KEY)
    sessionStorage.clear()
    setActiveBrand(null)
    setAvailableBrands([])

    const res = await api.register(payload)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    setToken(res.access_token)
    setUser(res.user)

    const allBrands = await api.listBrands()
    return resolveBrandState(allBrands, res.user)
  }

  const demoLogin = async (role: 'admin' | 'creator' | 'reviewer'): Promise<BrandRoutingResult> => {
    // Clear previous user session and brand context before switching demo roles
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ACTIVE_BRAND_KEY)
    sessionStorage.clear()
    setToken(null)
    setUser(null)
    setActiveBrand(null)
    setAvailableBrands([])

    const email = role === 'creator' ? 'editor@lumacare.demo' : `${role}@lumacare.demo`
    const password = import.meta.env.VITE_DEMO_SEED_PASSWORD || 'LumaCareDemo2026!'
    return login({ email, password })
  }

  const switchBrand = (brand: BrandSummary) => {
    const isAuth = availableBrands.some((b) => b.id === brand.id)
    if (!isAuth) {
      throw new Error(`Unauthorized brand access attempt: ${brand.id}`)
    }
    setActiveBrand(brand)
    localStorage.setItem(ACTIVE_BRAND_KEY, brand.id)
  }

  const selectBrandById = (brandId: string): boolean => {
    const found = availableBrands.find((b) => b.id === brandId)
    if (found) {
      switchBrand(found)
      return true
    }
    return false
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        activeBrand,
        availableBrands,
        login,
        register,
        demoLogin,
        logout,
        switchBrand,
        selectBrandById,
        refreshBrands,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
