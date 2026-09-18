"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Shield, Mail, Lock, Eye, EyeOff } from "lucide-react"
import { api, setToken, type User } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { Separator } from "@/components/ui/separator"
import { useNavigate } from "react-router-dom"

interface LoginProps {
  onLogin: (user: User) => void
}

export function Login({ onLogin }: LoginProps) {
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const res = await api.auth.login(username, password)
      setToken(res.access_token)
      onLogin(res.user)
      navigate("/app/upload")
    } catch (err: any) {
      setError(err.message || "Login failed")
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (user: string, pass: string) => {
    setUsername(user)
    setPassword(pass)
    setError("")
    setLoading(true)
    try {
      const res = await api.auth.login(user, pass)
      setToken(res.access_token)
      onLogin(res.user)
      navigate("/app/upload")
    } catch (err: any) {
      setError(err.message || "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10"
          >
            <Shield className="h-7 w-7 text-primary" />
          </motion.div>
          <h1 className="font-display text-3xl font-bold text-foreground mb-2">Welcome back</h1>
          <p className="text-muted-foreground">Sign in to analyze your legal documents</p>
        </div>

        <ScrollReveal className="bg-card border border-border rounded-2xl p-6 md:p-8">
          <StaggerContainer staggerDelay={0.08}>
            <StaggerItem direction="up">
              <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm"
                  >
                    <svg className="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    {error}
                  </motion.div>
                )}

                <StaggerItem direction="up">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                      <Input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter username"
                        className="pl-10"
                        disabled={loading}
                        required
                      />
                    </div>
                  </div>
                </StaggerItem>

                <StaggerItem direction="up">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password">Password</Label>
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter password"
                        className="pl-10 pr-10"
                        disabled={loading}
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                  </div>
                </StaggerItem>

                <StaggerItem direction="up">
                  <Button type="submit" className="w-full py-3" disabled={loading}>
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Signing in...
                      </span>
                    ) : (
                      "Sign In"
                    )}
                  </Button>
                </StaggerItem>
              </form>
            </StaggerItem>

            <StaggerItem direction="up">
              <Separator className="my-6" />
            </StaggerItem>

            <StaggerItem direction="up">
              <p className="text-center text-sm text-muted-foreground mb-4">Quick demo access</p>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Employee (India)", user: "asha", pass: "demo123" },
                  { label: "HR Manager", user: "priya", pass: "demo123" },
                  { label: "Legal Admin", user: "admin", pass: "demo123" },
                  { label: "Compliance", user: "marcus", pass: "demo123" },
                ].map((d) => (
                  <Button
                    key={d.user}
                    variant="outline"
                    size="sm"
                    onClick={() => quickLogin(d.user, d.pass)}
                    disabled={loading}
                    className="text-sm h-auto py-2.5"
                  >
                    {d.label}
                  </Button>
                ))}
              </div>
            </StaggerItem>
          </StaggerContainer>
        </ScrollReveal>

        <p className="text-center text-sm text-muted-foreground mt-6">
          By signing in, you agree to our{" "}
          <a href="#" className="text-primary hover:underline">Terms of Service</a>{" "}
          and{" "}
          <a href="#" className="text-primary hover:underline">Privacy Policy</a>
        </p>
      </div>
    </div>
  )
}