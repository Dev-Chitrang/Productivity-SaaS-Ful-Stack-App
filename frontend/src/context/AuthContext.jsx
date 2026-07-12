import { createContext, useContext, useState, useEffect, useCallback } from "react"
import { userApi } from "@/features/auth/services/authApi"
import { clearGuestSession } from "@/features/meetings/utils/guestSession"
import { getBrowserTimezone } from "@/lib/timezone"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      setIsLoading(false)
      return
    }
    try {
      const { data } = await userApi.getProfile()

      // One-time automatic timezone sync for existing and new users.
      // If the backend returned null (no preference set yet), silently push
      // the browser timezone. No toast, no user interaction required.
      if (!data.timezone) {
        const browserTz = getBrowserTimezone()
        try {
          const { data: updated } = await userApi.updateProfile({ timezone: browserTz })
          setUser(updated)
        } catch {
          // Non-critical — set user with null timezone; fallback logic in forms handles it.
          setUser(data)
        }
      } else {
        setUser(data)
      }
    } catch {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const loginTokens = (tokens) => {
    localStorage.setItem("access_token", tokens.access_token)
    localStorage.setItem("refresh_token", tokens.refresh_token)
    fetchUser()
  }

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    clearGuestSession()
    setUser(null)
  }

  const refreshUser = () => fetchUser()

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated, loginTokens, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuthContext must be used within AuthProvider")
  return ctx
}
