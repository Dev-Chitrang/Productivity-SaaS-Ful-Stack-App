import { Link } from "react-router-dom"
import ResetPasswordForm from "../components/ResetPasswordForm"

function ResetPasswordPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <h1 className="text-lg font-semibold tracking-tight">Set new password</h1>
        <p className="text-xs text-muted-foreground">
          Choose a new password for your account.
        </p>
      </div>
      <ResetPasswordForm />
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

export default ResetPasswordPage
