import { createContext, useContext, useState, useEffect, useCallback } from "react"
import { userApi } from "@/features/auth/services/authApi"

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
      setUser(data)
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
