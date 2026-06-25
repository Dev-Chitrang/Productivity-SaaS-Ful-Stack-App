import { Link } from "react-router-dom"
import ForgotPasswordForm from "../components/ForgotPasswordForm"

function ForgotPasswordPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <h1 className="text-lg font-semibold tracking-tight">Reset password</h1>
        <p className="text-xs text-muted-foreground">
          Enter your email and we&apos;ll send you a reset link.
        </p>
      </div>
      <ForgotPasswordForm />
      <p className="text-center text-xs text-muted-foreground">
        <Link
          to="/login"
          className="hover:text-foreground transition-colors"
        >
          Back to sign in
        </Link>
      </p>
    </div>
  )
}

export default ForgotPasswordPage
