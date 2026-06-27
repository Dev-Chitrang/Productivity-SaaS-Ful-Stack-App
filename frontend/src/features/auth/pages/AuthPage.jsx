import { useState, useEffect, useCallback, useRef } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { motion } from "framer-motion"
import {
  Mail, Lock, User, Eye, EyeOff, ArrowRight, Check, Sparkles, ArrowLeft,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ThemeToggle } from "@/components/ThemeToggle"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { useLogin, useSignup, useGoogleOAuth } from "../hooks/useAuth"
import { useAuthContext } from "@/context/AuthContext"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { GoogleButton, OrDivider } from "../components/GoogleButton"

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const signupSchema = z
  .object({
    full_name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
    enable_2fa: z.boolean().default(false),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  })

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
})

const otpSchema = z.object({
  code: z
    .string()
    .length(6, "Code must be exactly 6 digits")
    .regex(/^\d+$/, "Code must contain only numbers"),
})

// ---------------------------------------------------------------------------
// Animation constants
// ---------------------------------------------------------------------------

const transition = { duration: 0.325, ease: [0.16, 1, 0.3, 1] }

// ---------------------------------------------------------------------------
// SignupForm
// ---------------------------------------------------------------------------

function SignupForm({ onOtpSent, onLoginSuccess }) {
  const { signupMutation } = useSignup()
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const { signIn: googleSignIn, isPending: googlePending } = useGoogleOAuth({
    onOtpRequired: (token, mode) => onOtpSent(token, mode),
    onSuccess: onLoginSuccess,
  })

  const form = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: { full_name: "", email: "", password: "", confirmPassword: "", enable_2fa: false },
  })

  async function onSubmit(values) {
    try {
      const { confirmPassword, ...payload } = values
      const { data } = await signupMutation.mutateAsync(payload)
      if (data?.verification_token) {
        onOtpSent(data.verification_token, "signup")
      }
    } catch { }
  }

  return (
    <div className="space-y-4">
      <GoogleButton onClick={googleSignIn} isLoading={googlePending} />
      <OrDivider />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField control={form.control} name="full_name" render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <div className="relative">
                  <User className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input placeholder="John Doe" className="h-10 pl-9" {...field} />
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="email" render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input placeholder="you@example.com" className="h-10 pl-9" {...field} />
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="password" render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="At least 8 characters"
                    className="h-10 pl-9 pr-9"
                    {...field}
                  />
                  <button
                    type="button"
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center justify-center size-7 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                  </button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="confirmPassword" render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm password</FormLabel>
              <FormControl>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Repeat your password"
                    className="h-10 pl-9 pr-9"
                    {...field}
                  />
                  <button
                    type="button"
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center justify-center size-7 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                  </button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="enable_2fa" render={({ field }) => (
            <FormItem>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="signup_2fa"
                  checked={field.value}
                  onChange={(e) => field.onChange(e.target.checked)}
                  className="size-3.5 accent-primary"
                />
                <FormLabel htmlFor="signup_2fa" className="cursor-pointer text-xs font-normal text-muted-foreground">
                  Enable two-factor authentication
                </FormLabel>
              </div>
              <FormMessage />
            </FormItem>
          )} />
          <Button type="submit" className="w-full h-10 mt-2" disabled={signupMutation.isPending}>
            {signupMutation.isPending ? "Creating account..." : "Create account"}
            <ArrowRight className="size-3.5 ml-1" />
          </Button>
        </form>
      </Form>
    </div>
  )
}

// ---------------------------------------------------------------------------
// LoginForm
// ---------------------------------------------------------------------------

function LoginForm({ onOtpSent, onLoginSuccess }) {
  const { loginMutation } = useLogin()
  const [showPassword, setShowPassword] = useState(false)

  const { signIn: googleSignIn, isPending: googlePending } = useGoogleOAuth({
    onOtpRequired: (token, mode) => onOtpSent(token, mode),
    onSuccess: onLoginSuccess,
  })

  const form = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  })

  async function onSubmit(values) {
    try {
      const { data } = await loginMutation.mutateAsync(values)
      if (data.requires_2fa && data.verification_token) {
        onOtpSent(data.verification_token, "login")
      } else if (data.access_token) {
        onLoginSuccess(data)
      }
    } catch { }
  }

  return (
    <div className="space-y-4">
      <GoogleButton onClick={googleSignIn} isLoading={googlePending} />
      <OrDivider />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField control={form.control} name="email" render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input placeholder="you@example.com" className="h-10 pl-9" {...field} />
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="password" render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    className="h-10 pl-9 pr-9"
                    {...field}
                  />
                  <button
                    type="button"
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center justify-center size-7 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                  </button>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <div className="text-right pt-1">
            <Link
              to="/forgot-password"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <Button type="submit" className="w-full h-10" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Signing in..." : "Sign in"}
            <ArrowRight className="size-3.5 ml-1" />
          </Button>
        </form>
      </Form>
    </div>
  )
}

// ---------------------------------------------------------------------------
// OtpCard — unchanged, reused for both email and Google 2FA paths
// ---------------------------------------------------------------------------

function OtpCard({ verificationToken, mode, onBack, onSignupVerified }) {
  const { verifyMutation: verifySignup, resendMutation: resendSignup } = useSignup()
  const { verifyMutation: verifyLogin, resendMutation: resendLogin } = useLogin()
  const verifyMutation = mode === "signup" ? verifySignup : verifyLogin
  const resendMutation = mode === "signup" ? resendSignup : resendLogin
  const [countdown, setCountdown] = useState(120)
  const intervalRef = useRef(null)

  const form = useForm({
    resolver: zodResolver(otpSchema),
    defaultValues: { code: "" },
  })

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(intervalRef.current)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(intervalRef.current)
  }, [])

  const resetCountdown = useCallback(() => {
    setCountdown(120)
    clearInterval(intervalRef.current)
    intervalRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(intervalRef.current)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [])

  function onSubmit(values) {
    verifyMutation.mutate(
      { verification_token: verificationToken, code: values.code },
    )
  }

  function handleResend() {
    resendMutation.mutate(
      { verification_token: verificationToken },
      { onSuccess: resetCountdown },
    )
  }

  const showSuccess = verifyMutation.isSuccess && mode === "signup"

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 p-4 backdrop-blur-md"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        className="w-[440px] bg-card px-10 py-10 rounded-xl shadow-2xl ring-1 ring-border"
      >
        {showSuccess ? (
          <div className="text-center">
            <div className="mb-4 flex justify-center">
              <div className="flex size-12 items-center justify-center rounded-full bg-muted">
                <Check className="size-6 text-primary" />
              </div>
            </div>
            <h2 className="text-lg font-semibold text-card-foreground">Email verified</h2>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Your account is ready. Please sign in to continue.
            </p>
            <Button className="mt-6" onClick={onSignupVerified}>
              Go to sign in
            </Button>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-card-foreground">
                {mode === "signup" ? "Verify your email" : "Two-factor authentication"}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {mode === "signup"
                  ? "Enter the 6-digit code sent to your email."
                  : "Enter the 6-digit code sent to your email to complete login."}
              </p>
            </div>

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
                <FormField control={form.control} name="code" render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      <Input
                        placeholder="000000"
                        maxLength={6}
                        className="h-14 text-center text-xl tracking-[0.5em] font-mono"
                        autoComplete="one-time-code"
                        inputMode="numeric"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <Button type="submit" className="w-full h-10" disabled={verifyMutation.isPending}>
                  {verifyMutation.isPending
                    ? "Verifying..."
                    : mode === "signup"
                      ? "Verify email"
                      : "Verify login"}
                  <Check className="size-3.5 ml-1" />
                </Button>
                <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground">
                  {countdown > 0 ? (
                    <span>
                      Resend code in {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, "0")}
                    </span>
                  ) : (
                    <button
                      type="button"
                      className="text-sm text-primary hover:text-primary/80 transition-colors"
                      disabled={resendMutation.isPending}
                      onClick={handleResend}
                    >
                      {resendMutation.isPending ? "Resending..." : "Resend code"}
                    </button>
                  )}
                </div>
              </form>
            </Form>

            <button
              type="button"
              onClick={onBack}
              className="mt-6 w-full text-center text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Back to {mode === "signup" ? "sign up" : "sign in"}
            </button>
          </>
        )}
      </motion.div>
    </motion.div>
  )
}

// ---------------------------------------------------------------------------
// AuthPage
// ---------------------------------------------------------------------------

function AuthPage() {
  const { isAuthenticated, loginTokens } = useAuthContext()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // Read initial mode from URL, default to login
  const modeParam = searchParams.get("mode")
  const [activeCard, setActiveCard] = useState(
    modeParam === "signup" ? "signup" : "login",
  )

  const [otpState, setOtpState] = useState({ show: false, token: null, mode: "signup" })

  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard", { replace: true })
  }, [isAuthenticated, navigate])

  // Sync URL param with activeCard
  useEffect(() => {
    setSearchParams({ mode: activeCard }, { replace: true })
  }, [activeCard, setSearchParams])

  function handleOtpSent(token, mode) {
    setOtpState({ show: true, token, mode })
  }

  function handleOtpBack() {
    setOtpState({ show: false, token: null, mode: "signup" })
  }

  function handleSignupVerified() {
    setOtpState({ show: false, token: null, mode: "signup" })
    setActiveCard("login")
  }

  function handleLoginSuccess(tokens) {
    loginTokens(tokens)
    navigate("/dashboard")
  }

  const signupInactive = activeCard !== "signup"
  const loginInactive = activeCard !== "login"

  return (
    <div className="relative min-h-screen bg-background flex flex-col items-center justify-center px-6 py-12">
      {/* Top bar with back link and theme toggle */}
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-3">
        <Link
          to="/"
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Back to home"
        >
          <ArrowLeft className="size-3.5" />
          Home
        </Link>
        <ThemeToggle />
      </div>
      {otpState.show && (
        <OtpCard
          verificationToken={otpState.token}
          mode={otpState.mode}
          onBack={handleOtpBack}
          onSignupVerified={handleSignupVerified}
        />
      )}

      <div className="mb-10 text-center">
        <div className="mb-3 flex justify-center">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-primary shadow-lg">
            <Sparkles className="size-6 text-primary-foreground" />
          </div>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Unified Workspace
        </h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Meetings, Notes, Tasks and Calendar in one place.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row items-start justify-center gap-6 lg:gap-8 w-full max-w-[1024px]">
        {/* ---- Signup card ---- */}
        <motion.div
          layout
          animate={{
            scale: signupInactive ? 0.94 : 1,
            opacity: signupInactive ? 0.55 : 1,
            filter: signupInactive ? "blur(3px)" : "blur(0px)",
            x: signupInactive ? -16 : 0,
            zIndex: signupInactive ? 10 : 20,
          }}
          transition={transition}
          style={{
            boxShadow: signupInactive
              ? "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06)"
              : "0 25px 50px -12px rgba(0,0,0,0.25)"
          }}
          onClick={() => { if (signupInactive) setActiveCard("signup") }}
          className="relative w-full lg:w-[460px] xl:w-[480px] bg-card rounded-xl p-8 sm:p-10 cursor-default"
        >
          <div className={signupInactive ? "pointer-events-none" : ""}>
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-card-foreground">Create account</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Fill in the details to get started.
              </p>
            </div>
            <SignupForm onOtpSent={handleOtpSent} onLoginSuccess={handleLoginSuccess} />
            <p className="mt-6 text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setActiveCard("login") }}
                className="text-primary hover:text-primary/80 transition-colors font-medium"
              >
                Sign in
              </button>
            </p>
          </div>
        </motion.div>

        {/* ---- Login card ---- */}
        <motion.div
          layout
          animate={{
            scale: loginInactive ? 0.94 : 1,
            opacity: loginInactive ? 0.55 : 1,
            filter: loginInactive ? "blur(3px)" : "blur(0px)",
            x: loginInactive ? 16 : 0,
            zIndex: loginInactive ? 10 : 20,
          }}
          transition={transition}
          style={{
            boxShadow: loginInactive
              ? "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06)"
              : "0 25px 50px -12px rgba(0,0,0,0.25)"
          }}
          onClick={() => { if (loginInactive) setActiveCard("login") }}
          className="relative w-full lg:w-[460px] xl:w-[480px] bg-card rounded-xl p-8 sm:p-10 cursor-default"
        >
          <div className={loginInactive ? "pointer-events-none" : ""}>
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-card-foreground">Sign in</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Enter your credentials to access your account.
              </p>
            </div>
            <LoginForm onOtpSent={handleOtpSent} onLoginSuccess={handleLoginSuccess} />
            <p className="mt-6 text-center text-sm text-muted-foreground">
              Don&apos;t have an account?{" "}
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setActiveCard("signup") }}
                className="text-primary hover:text-primary/80 transition-colors font-medium"
              >
                Create account
              </button>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default AuthPage
