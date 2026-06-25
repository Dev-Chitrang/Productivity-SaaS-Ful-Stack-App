import { Routes, Route, Navigate } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"

import LandingPage from "../pages/LandingPage"
import AuthPage from "../features/auth/pages/AuthPage"
import ForgotPasswordPage from "../features/auth/pages/ForgotPasswordPage"
import ResetPasswordPage from "../features/auth/pages/ResetPasswordPage"
import DashboardPage from "../features/dashboard/pages/DashboardPage"
import ProfilePage from "../features/profile/pages/ProfilePage"
import SettingsPage from "../features/settings/pages/SettingsPage"
import AuthLayout from "../layouts/AuthLayout"

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthContext()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/auth" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route element={<AuthLayout />}>
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
    </Routes>
  )
}

export default AppRoutes
