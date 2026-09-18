import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { Landing } from "@/components/landing/Landing"
import { AppLayout } from "@/components/app/AppLayout"
import { Login } from "@/components/app/Login"
import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Shield, Loader2 } from "lucide-react"

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    setChecking(false)
  }, [])

  if (checking) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="min-h-screen flex items-center justify-center bg-background"
      >
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <Shield className="h-7 w-7 text-primary" />
          </div>
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </motion.div>
    )
  }

  return <>{children}</>
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("legallens_token")
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("legallens_token")
  if (token) {
    return <Navigate to="/app/upload" replace />
  }
  return <>{children}</>
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route
            path="/app/*"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

function LoginPage() {
  const [user, setUser] = useState<{ name: string } | null>(null)

  if (user) {
    return <Navigate to="/app/upload" replace />
  }

  return <Login onLogin={setUser} />
}