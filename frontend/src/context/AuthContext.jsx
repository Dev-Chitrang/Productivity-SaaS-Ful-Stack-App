import { createContext, useContext, useState, useEffect, useCallback } from "react"
import { userApi } from "@/features/auth/services/authApi"
import { clearGuestSession } from "@/features/meetings/utils/guestSession"
import { getBrowserTimezone } from "@/lib/timezone"
import { getAccessToken, setAccessToken, clearAccessToken } from "@/lib/tokenStore"
import api from "@/lib/axios"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  const fetchUser = useCallback(async () => {
    const token = getAccessToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    try {
      const { data } = await userApi.getProfile()

      if (!data.timezone) {
        const browserTz = getBrowserTimezone()
        try {
          const { data: updated } = await userApi.updateProfile({ timezone: browserTz })
          setUser(updated)
        } catch {
          setUser(data)
        }
      } else {
        setUser(data)
      }
    } catch {
      clearAccessToken()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const loginTokens = (tokens) => {
    setAccessToken(tokens.access_token)
    fetchUser()
  }

  const logout = async () => {
    try {
      await api.post("/auth/logout")
    } catch {
      // proceed with client-side cleanup regardless
    }
    clearAccessToken()
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
