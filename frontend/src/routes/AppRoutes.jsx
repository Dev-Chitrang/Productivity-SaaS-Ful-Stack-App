import { Routes, Route, Navigate, useLocation } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"
import { hasGuestSessionForMeeting } from "@/features/meetings/utils/guestSession"

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
import WhiteboardPage from "../features/whiteboards/pages/WhiteboardPage"
import MeetingsPage from "../features/meetings/pages/MeetingsPage"
import MeetingDetailPage from "../features/meetings/pages/MeetingDetailPage"
import MeetingRoomPage from "../features/meetings/pages/MeetingRoomPage"
import MeetingJoinPage from "../features/meetings/pages/MeetingJoinPage"
import AuthLayout from "../layouts/AuthLayout"
import MainLayout from "../layouts/MainLayout"

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthContext()
  const location = useLocation()
  if (isLoading) return null
  if (!isAuthenticated) {
    const match = location.pathname.match(/^\/meetings\/([^/]+)/)
    if (match) {
      const meetingId = match[1]
      if (hasGuestSessionForMeeting(meetingId)) {
        return children
      }
      return (
        <Navigate
          to={`/auth?mode=login&meetingId=${meetingId}&redirect=${encodeURIComponent(location.pathname)}`}
          replace
        />
      )
    }
    return <Navigate to="/auth" replace />
  }
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/m/:meetingCode" element={<MeetingJoinPage />} />
      <Route element={<AuthLayout />}>
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>
      <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/notes" element={<NotesPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/meetings" element={<MeetingsPage />} />
        <Route path="/meetings/:id" element={<MeetingDetailPage />} />
        <Route path="/meetings/:id/room" element={<MeetingRoomPage />} />
        <Route path="/whiteboards" element={<WhiteboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default AppRoutes
