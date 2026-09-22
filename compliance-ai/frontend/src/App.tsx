import { useState } from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { Landing } from "@/components/landing/Landing"
import { AppLayout } from "@/components/app/AppLayout"
import { Login } from "@/components/app/Login"

function AuthProvider({ children }: { children: React.ReactNode }) {
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