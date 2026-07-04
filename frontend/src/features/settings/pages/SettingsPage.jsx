import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Mail, Lock, Eye, EyeOff } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Separator } from "@/components/ui/separator"
import { useAuthContext } from "@/context/AuthContext"
import {
  useChangeEmail,
  useChangePassword,
  useToggle2FA,
} from "@/hooks/useUserApi"
import ReminderSettings from "@/features/settings/components/ReminderSettings"

const emailSchema = z.object({
  current_password: z.string().min(1, "Password is required"),
  new_email: z.string().email("Invalid email address"),
})

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  })

function SettingsPage() {
  const { user } = useAuthContext()
  const changeEmailMutation = useChangeEmail()
  const changePasswordMutation = useChangePassword()
  const toggle2FAMutation = useToggle2FA()
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const emailForm = useForm({
    resolver: zodResolver(emailSchema),
    defaultValues: { current_password: "", new_email: "" },
  })

  const passwordForm = useForm({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: "", new_password: "", confirm_password: "" },
  })

  function onEmailSubmit(values) {
    changeEmailMutation.mutate(values, {
      onSuccess: () => emailForm.reset(),
    })
  }

  function onPasswordSubmit(values) {
    changePasswordMutation.mutate(
      { current_password: values.current_password, new_password: values.new_password },
      { onSuccess: () => passwordForm.reset() }
    )
  }

  return (
    <main className="mx-auto max-w-lg px-6 py-8">
        <div className="space-y-8">
          {/* Change Email */}
          <section>
            <h2 className="mb-4 text-sm font-semibold tracking-tight">Change email</h2>
            <Form {...emailForm}>
              <form onSubmit={emailForm.handleSubmit(onEmailSubmit)} className="space-y-3">
                <FormField control={emailForm.control} name="new_email" render={({ field }) => (
                  <FormItem>
                    <FormLabel>New email</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Mail className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                        <Input placeholder="new@example.com" className="pl-8" {...field} />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={emailForm.control} name="current_password" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                        <Input type={showCurrent ? "text" : "password"} placeholder="Confirm your password" className="pl-8 pr-8" {...field} />
                        <button type="button" className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center justify-center size-6 text-muted-foreground hover:text-foreground" onClick={() => setShowCurrent(!showCurrent)} tabIndex={-1}>
                          {showCurrent ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <Button type="submit" size="sm" disabled={changeEmailMutation.isPending}>
                  {changeEmailMutation.isPending ? "Updating..." : "Update email"}
                </Button>
              </form>
            </Form>
          </section>

          {/* Change Password */}
          <section>
            <h2 className="mb-4 text-sm font-semibold tracking-tight">Change password</h2>
            <Form {...passwordForm}>
              <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-3">
                <FormField control={passwordForm.control} name="current_password" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                        <Input type="password" placeholder="Current password" className="pl-8" {...field} />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={passwordForm.control} name="new_password" render={({ field }) => (
                  <FormItem>
                    <FormLabel>New password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                        <Input type={showNew ? "text" : "password"} placeholder="At least 8 characters" className="pl-8 pr-8" {...field} />
                        <button type="button" className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center justify-center size-6 text-muted-foreground hover:text-foreground" onClick={() => setShowNew(!showNew)} tabIndex={-1}>
                          {showNew ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={passwordForm.control} name="confirm_password" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirm new password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                        <Input type={showConfirm ? "text" : "password"} placeholder="Repeat your password" className="pl-8 pr-8" {...field} />
                        <button type="button" className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center justify-center size-6 text-muted-foreground hover:text-foreground" onClick={() => setShowConfirm(!showConfirm)} tabIndex={-1}>
                          {showConfirm ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <Button type="submit" size="sm" disabled={changePasswordMutation.isPending}>
                  {changePasswordMutation.isPending ? "Updating..." : "Update password"}
                </Button>
              </form>
            </Form>
          </section>

          {/* Two-Factor Authentication */}
          <section>
            <h2 className="mb-4 text-sm font-semibold tracking-tight">Two-factor authentication</h2>
            <p className="mb-3 text-xs text-muted-foreground">
              {user?.is_2fa_enabled
                ? "2FA is currently enabled."
                : "2FA is currently disabled."}
            </p>
            <Button
              size="sm"
              variant={user?.is_2fa_enabled ? "outline" : "default"}
              onClick={() => toggle2FAMutation.mutate({ enable: !user?.is_2fa_enabled })}
              disabled={toggle2FAMutation.isPending}
            >
              {toggle2FAMutation.isPending
                ? "Updating..."
                : user?.is_2fa_enabled
                  ? "Disable 2FA"
                  : "Enable 2FA"}
            </Button>
          </section>

          <Separator />

          <ReminderSettings />
        </div>
      </main>
  )
}

export default SettingsPage
