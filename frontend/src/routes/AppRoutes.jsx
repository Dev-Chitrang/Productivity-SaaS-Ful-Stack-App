import { Routes, Route, Navigate } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"

import LandingPage from "../pages/LandingPage"
import AuthPage from "../features/auth/pages/AuthPage"
import ForgotPasswordPage from "../features/auth/pages/ForgotPasswordPage"
import ResetPasswordPage from "../features/auth/pages/ResetPasswordPage"
import DashboardPage from "../features/dashboard/pages/DashboardPage"
import ProfilePage from "../features/profile/pages/ProfilePage"
import SettingsPage from "../features/settings/pages/SettingsPage"
import CalendarPage from "../features/calendar/pages/CalendarPage"
import NotesPage from "../features/notes/pages/NotesPage"
import TasksPage from "../features/tasks/pages/TasksPage"
import AuthLayout from "../layouts/AuthLayout"
import MainLayout from "../layouts/MainLayout"

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
      <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/notes" element={<NotesPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default AppRoutes
