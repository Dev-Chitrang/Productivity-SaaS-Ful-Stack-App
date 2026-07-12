import { useMutation } from "@tanstack/react-query"
import { useCallback, useEffect, useRef } from "react"
import toast from "react-hot-toast"
import { useNavigate } from "react-router-dom"
import { authApi } from "../services/authApi"
import { useAuthContext } from "@/context/AuthContext"
import { mapAuthError } from "../utils/authErrorMapper"

export function useSignup() {
  const signupMutation = useMutation({
    mutationFn: authApi.signup,
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })

  const verifyMutation = useMutation({
    mutationFn: authApi.verifySignupOtp,
    onSuccess: () => {
      toast.success("Email verified successfully. Please sign in.")
    },
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })

  const resendMutation = useMutation({
    mutationFn: authApi.resendSignupOtp,
    onSuccess: () => {
      toast.success("Verification code resent.")
    },
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })

  return { signupMutation, verifyMutation, resendMutation }
}

export function useLogin({ redirectUrl } = {}) {
  const { loginTokens } = useAuthContext()
  const navigate = useNavigate()

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })

  const verifyMutation = useMutation({
    mutationFn: authApi.verifyLoginOtp,
    onSuccess: ({ data }) => {
      toast.success("Logged in successfully.")
      loginTokens(data)
      navigate(redirectUrl || "/dashboard")
    },
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })

  const resendMutation = useMutation({
    mutationFn: authApi.resendLoginOtp,
    onSuccess: () => {
      toast.success("Verification code resent.")
    },
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })

  return { loginMutation, verifyMutation, resendMutation }
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: authApi.forgotPassword,
    onSuccess: () => {
      toast.success("Check your email for reset instructions.")
    },
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })
}

export function useResetPassword() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: authApi.resetPassword,
    onSuccess: () => {
      toast.success("Password reset successfully.")
      navigate("/auth")
    },
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })
}

/**
 * Loads Google's Identity Services script once and provides a `signIn`
 * function that opens the One Tap / popup flow.  On success it calls
 * the backend and either issues JWT tokens or triggers the 2FA OTP modal.
 *
 * @param {object} options
 * @param {(token: string, mode: "login") => void} options.onOtpRequired - called when 2FA is needed
 * @param {(tokens: object) => void}               options.onSuccess     - called with tokens on direct login
 */
export function useGoogleOAuth({ onOtpRequired, onSuccess }) {
  const scriptLoadedRef = useRef(false)

  const googleMutation = useMutation({
    mutationFn: (id_token) => authApi.googleLogin(id_token),
    onError: (error) => {
      const mapped = mapAuthError(error)
      toast.error(mapped.message)
    },
  })

  // Inject the GSI script exactly once per page
  useEffect(() => {
    if (scriptLoadedRef.current || document.getElementById("google-gsi-script")) return
    const script = document.createElement("script")
    script.id = "google-gsi-script"
    script.src = "https://accounts.google.com/gsi/client"
    script.async = true
    script.defer = true
    document.head.appendChild(script)
    scriptLoadedRef.current = true
  }, [])

  const signIn = useCallback(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

    if (!clientId) {
      toast.error("Google OAuth is not configured.")
      return
    }

    const initAndPrompt = () => {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          if (!response.credential) {
            toast.error("Google sign-in was cancelled.")
            return
          }

          try {
            const { data } = await googleMutation.mutateAsync(response.credential)

            if (data.requires_2fa && data.verification_token) {
              onOtpRequired(data.verification_token, "login")
            } else if (data.access_token) {
              toast.success("Signed in with Google.")
              onSuccess(data)
            }
          } catch {
            // error toast already handled by onError above
          }
        },
        // Use popup so the user stays on the same page
        ux_mode: "popup",
      })

      window.google.accounts.id.prompt((notification) => {
        // If One Tap is suppressed (e.g., user previously dismissed it),
        // fall back to the explicit button-triggered OAuth flow.
        if (
          notification.isNotDisplayed() ||
          notification.isSkippedMoment()
        ) {
          window.google.accounts.oauth2
            ? window.google.accounts.id.renderButton(
              document.getElementById("google-signin-hidden-btn"),
              { theme: "outline", size: "large" }
            )
            : null

          // Trigger the select_account flow directly as fallback
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: async (response) => {
              if (!response.credential) {
                toast.error("Google sign-in was cancelled.")
                return
              }
              try {
                const { data } = await googleMutation.mutateAsync(response.credential)
                if (data.requires_2fa && data.verification_token) {
                  onOtpRequired(data.verification_token, "login")
                } else if (data.access_token) {
                  toast.success("Signed in with Google.")
                  onSuccess(data)
                }
              } catch { }
            },
            ux_mode: "popup",
            select_account: true,
          })
          window.google.accounts.id.prompt()
        }
      })
    }

    // If the script is already loaded, call immediately; otherwise wait for it
    if (window.google?.accounts?.id) {
      initAndPrompt()
    } else {
      const scriptEl = document.getElementById("google-gsi-script")
      const onLoad = () => {
        initAndPrompt()
        scriptEl?.removeEventListener("load", onLoad)
      }
      scriptEl?.addEventListener("load", onLoad)
    }
  }, [googleMutation, onOtpRequired, onSuccess])

  return { signIn, isPending: googleMutation.isPending }
}
