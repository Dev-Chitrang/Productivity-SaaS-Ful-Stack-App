import { useRef } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { User, Mail, Lock, Shield, Camera, ArrowLeft } from "lucide-react"
import { Link } from "react-router-dom"

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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useAuthContext } from "@/context/AuthContext"
import { useProfile } from "@/hooks/useUserApi"

const profileSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  timezone: z.string().optional(),
})

function ProfilePage() {
  const { user } = useAuthContext()
  const { profile, isLoading, updateMutation, imageMutation } = useProfile()
  const fileInputRef = useRef(null)

  const form = useForm({
    resolver: zodResolver(profileSchema),
    values: {
      full_name: profile?.full_name || user?.full_name || "",
      timezone: profile?.timezone || user?.timezone || "UTC",
    },
  })

  const initials = (profile?.full_name || user?.full_name || "?")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  function onSubmit(values) {
    updateMutation.mutate(values)
  }

  function handleImageUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onloadend = () => {
      const base64 = reader.result
      imageMutation.mutate({ profile_image: base64 })
    }
    reader.readAsDataURL(file)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <ProfileHeader />
        <main className="mx-auto max-w-lg px-6 py-12">
          <p className="text-sm text-muted-foreground">Loading...</p>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <ProfileHeader />
      <main className="mx-auto max-w-lg px-6 py-12">
        <div className="mb-8 flex flex-col items-center gap-4">
          <div className="relative">
            <Avatar size="lg">
              {(profile?.profile_image || user?.profile_image) ? (
                <AvatarImage src={profile?.profile_image || user?.profile_image} />
              ) : (
                <AvatarFallback className="text-sm font-medium">{initials}</AvatarFallback>
              )}
            </Avatar>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="absolute -right-1 -bottom-1 flex size-6 items-center justify-center rounded-full bg-primary text-primary-foreground ring-2 ring-background"
            >
              <Camera className="size-3" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleImageUpload}
            />
          </div>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField control={form.control} name="full_name" render={({ field }) => (
              <FormItem>
                <FormLabel>Full Name</FormLabel>
                <FormControl>
                  <div className="relative">
                    <User className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                    <Input className="pl-8" {...field} />
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />
            <FormItem>
              <FormLabel>Email</FormLabel>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                <Input className="pl-8" value={profile?.email || user?.email || ""} disabled />
              </div>
            </FormItem>
            <FormItem>
              <FormLabel>Password</FormLabel>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                <Input className="pl-8" type="password" value="••••••••" disabled />
              </div>
            </FormItem>
            <FormItem>
              <FormLabel>Two-Factor Authentication</FormLabel>
              <div className="flex items-center gap-2 text-xs">
                <Shield className="size-3.5 text-muted-foreground" />
                <span>
                  {profile?.is_2fa_enabled || user?.is_2fa_enabled ? "Enabled" : "Disabled"}
                </span>
              </div>
            </FormItem>
            <div className="flex gap-2">
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "Saving..." : "Save changes"}
              </Button>
            </div>
          </form>
        </Form>
      </main>
    </div>
  )
}

function ProfileHeader() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="size-4" />
          </Link>
          <span className="text-sm font-semibold tracking-tight">Profile</span>
        </div>
      </div>
    </header>
  )
}

export default ProfilePage
