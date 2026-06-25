import api from "@/lib/axios"

export const authApi = {
  signup: (data) => api.post("/auth/signup", data),
  verifySignupOtp: (data) => api.post("/auth/verify-signup", data),
  resendSignupOtp: (data) => api.post("/auth/resend-signup-otp", data),
  login: (data) => api.post("/auth/login", data),
  verifyLoginOtp: (data) => api.post("/auth/verify-login", data),
  resendLoginOtp: (data) => api.post("/auth/resend-login-otp", data),
  refresh: (data) => api.post("/auth/refresh", data),
  forgotPassword: (data) => api.post("/auth/password-reset/initiate", data),
  resetPassword: (data) => api.post("/auth/password-reset/confirm", data),
  /** Sends a verified Google ID Token to the backend for login/signup. */
  googleLogin: (id_token) => api.post("/auth/google", { id_token }),
}

export const userApi = {
  getProfile: () => api.get("/users/me"),
  updateProfile: (data) => api.put("/users/profile", data),
  changePassword: (data) => api.put("/users/change-password", data),
  changeEmail: (data) => api.put("/users/change-email", data),
  updateProfileImage: (data) => api.put("/users/profile-image", data),
  toggle2fa: (data) => api.put("/users/2fa", data),
  deactivate: () => api.delete("/users/deactivate"),
}
