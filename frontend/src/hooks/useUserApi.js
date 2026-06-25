import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import { useNavigate } from "react-router-dom"
import { userApi } from "@/features/auth/services/authApi"
import { useAuthContext } from "@/context/AuthContext"

export function useProfile() {
  const { refreshUser } = useAuthContext()

  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => userApi.getProfile().then((r) => r.data),
    staleTime: 30000,
  })

  const updateMutation = useMutation({
    mutationFn: userApi.updateProfile,
    onSuccess: () => {
      toast.success("Profile updated.")
      refreshUser()
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || "Update failed."
      toast.error(message)
    },
  })

  const imageMutation = useMutation({
    mutationFn: userApi.updateProfileImage,
    onSuccess: () => {
      toast.success("Profile image updated.")
      refreshUser()
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || "Upload failed."
      toast.error(message)
    },
  })

  return { profile, isLoading, updateMutation, imageMutation }
}

export function useChangePassword() {
  const { logout } = useAuthContext()

  return useMutation({
    mutationFn: userApi.changePassword,
    onSuccess: () => {
      toast.success("Password changed. Please log in again.")
      logout()
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || "Change failed."
      toast.error(message)
    },
  })
}

export function useChangeEmail() {
  const { logout } = useAuthContext()

  return useMutation({
    mutationFn: userApi.changeEmail,
    onSuccess: () => {
      toast.success("Email changed. Please log in again.")
      logout()
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || "Change failed."
      toast.error(message)
    },
  })
}

export function useToggle2FA() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: userApi.toggle2fa,
    onSuccess: () => {
      toast.success("2FA settings updated.")
      queryClient.invalidateQueries({ queryKey: ["profile"] })
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || "Update failed."
      toast.error(message)
    },
  })
}

export function useDeactivate() {
  const { logout } = useAuthContext()

  return useMutation({
    mutationFn: userApi.deactivate,
    onSuccess: () => {
      toast.success("Account deactivated.")
      logout()
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || "Deactivation failed."
      toast.error(message)
    },
  })
}
