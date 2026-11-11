/**
 * Authentication and Multi-Tenant Workspace Context.
 * Manages user session, JWT persistence, role-based state, and active brand workspace.
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type {
  BrandSummary,
  UserLoginRequest,
  UserRegisterRequest,
  UserResponse,
} from '../api/types'

interface AuthContextType {
  user: UserResponse | null
  token: string | null
  isLoading: boolean
  activeBrand: BrandSummary | null
  availableBrands: BrandSummary[]
  login: (payload: UserLoginRequest) => Promise<void>
  register: (payload: UserRegisterRequest) => Promise<void>
  logout: () => void
  switchBrand: (brand: BrandSummary) => void
  refreshBrands: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'inkloom_token'
const ACTIVE_BRAND_KEY = 'inkloom_active_brand_id'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [availableBrands, setAvailableBrands] = useState<BrandSummary[]>([])
  const [activeBrand, setActiveBrand] = useState<BrandSummary | null>(null)

  const refreshBrands = async () => {
    try {
      const brands = await api.listBrands()
      setAvailableBrands(brands)

      const savedBrandId = localStorage.getItem(ACTIVE_BRAND_KEY)
      if (savedBrandId) {
        const found = brands.find((b) => b.id === savedBrandId)
        if (found) {
          setActiveBrand(found)
          return
        }
      }

      // Default to demo brand or first available
      const demo = brands.find((b) => b.is_demo)
      if (demo) {
        setActiveBrand(demo)
      } else if (brands.length > 0) {
        setActiveBrand(brands[0])
      }
    } catch {
      // Brands fetch failed
    }
  }

  // Initialize session
  useEffect(() => {
    let mounted = true

    async function initAuth() {
      setIsLoading(true)
      const storedToken = localStorage.getItem(TOKEN_KEY)
      if (storedToken) {
        try {
          const profile = await api.getMe()
          if (mounted) {
            setUser(profile)
            setToken(storedToken)
          }
        } catch {
          if (mounted) {
            localStorage.removeItem(TOKEN_KEY)
            setToken(null)
            setUser(null)
          }
        }
      }
      await refreshBrands()
      if (mounted) setIsLoading(false)
    }

    initAuth()

    return () => {
      mounted = false
    }
  }, [token])

  const login = async (payload: UserLoginRequest) => {
    const res = await api.login(payload)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    setToken(res.access_token)
    setUser(res.user)
    await refreshBrands()
  }

  const register = async (payload: UserRegisterRequest) => {
    const res = await api.register(payload)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    setToken(res.access_token)
    setUser(res.user)
    await refreshBrands()
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
    refreshBrands()
  }

  const switchBrand = (brand: BrandSummary) => {
    setActiveBrand(brand)
    localStorage.setItem(ACTIVE_BRAND_KEY, brand.id)
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
        logout,
        switchBrand,
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
