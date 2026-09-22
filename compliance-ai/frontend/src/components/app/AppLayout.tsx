"use client"

import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Shield, LogOut, Upload, Search, GitCompare, FileSearch, MessageCircle, Sun, Moon, Menu, X, FileText, CheckCircle2, BookOpen } from "lucide-react"
import { useNavigate, useLocation, Link } from "react-router-dom"
import { api, clearToken, type DocumentInfo, type User } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel } from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useTheme } from "@/hooks"
import { DocumentXRay } from "./DocumentXRay"
import { ContractCompare } from "./ContractCompare"
import { LawyerBrief } from "./LawyerBrief"
import { LegalChat } from "./LegalChat"
import { UploadView } from "./UploadView"
import { LegalGlossary } from "./LegalGlossary"

type View = "upload" | "xray" | "compare" | "brief" | "chat" | "glossary"

const navItems: { id: View; label: string; icon: React.ReactNode; href: string }[] = [
  { id: "upload", label: "Upload & Analyze", icon: <Upload className="h-4 w-4" />, href: "/app/upload" },
  { id: "xray", label: "Document X-Ray", icon: <Search className="h-4 w-4" />, href: "/app/xray" },
  { id: "compare", label: "Contract Compare", icon: <GitCompare className="h-4 w-4" />, href: "/app/compare" },
  { id: "brief", label: "Lawyer Brief", icon: <FileSearch className="h-4 w-4" />, href: "/app/brief" },
  { id: "chat", label: "Legal Q&A", icon: <MessageCircle className="h-4 w-4" />, href: "/app/chat" },
  { id: "glossary", label: "Legal Glossary", icon: <BookOpen className="h-4 w-4" />, href: "/app/glossary" },
]

export function AppLayout() {
  const [user, setUser] = useState<User | null>(null)
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const token = localStorage.getItem("legallens_token")
    if (token) {
      api.auth.me().then((res) => {
        setUser(res)
        loadDocuments()
      }).catch(() => {
        clearToken()
        navigate("/login")
      })
    } else {
      navigate("/login")
    }
  }, [navigate])

  async function loadDocuments() {
    try {
      const res = await api.documents.list()
      setDocuments(res.documents || [])
    } catch {
      /* ignore */
    }
  }

  // Focus management & Escape key listener for accessible mobile menu dialog
  useEffect(() => {
    if (mobileMenuOpen) {
      const timer = setTimeout(() => {
        const firstLink = document.querySelector<HTMLElement>("[role='dialog'] a")
        firstLink?.focus()
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [mobileMenuOpen])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (!mobileMenuOpen) return
      if (e.key === "Escape") {
        setMobileMenuOpen(false)
        return
      }
      if (e.key === "Tab") {
        const dialog = document.querySelector<HTMLElement>("[role='dialog']")
        if (!dialog) return
        const focusable = dialog.querySelectorAll<HTMLElement>("a, button, [tabindex='0']")
        if (focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [mobileMenuOpen])

  function handleLogout() {
    clearToken()
    setUser(null)
    navigate("/login")
  }

  const currentView = navItems.find((item) => location.pathname === item.href)?.id || "upload"

  if (!user) return null

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Skip navigation for keyboard / screen reader users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[9999] focus:bg-primary focus:text-primary-foreground focus:px-4 focus:py-2 focus:rounded-lg focus:font-semibold"
      >
        Skip to main content
      </a>
      {/* Permanent Left Sidebar on Desktop */}
      <aside className="hidden md:flex h-full w-64 shrink-0 flex-col border-r border-border/80 bg-card">
        {/* Sidebar Brand Header */}
        <div className="flex h-16 items-center gap-3 px-5 border-b border-border/80">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/15 border border-primary/30 text-primary shadow-sm">
            <Shield className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-heading text-lg font-bold tracking-tight text-foreground leading-tight">
              LegalLens
            </span>
            <span className="text-[10px] font-semibold text-primary uppercase tracking-wider leading-none">
              AI Intelligence
            </span>
          </div>
        </div>

        {/* Sidebar Navigation Menu */}
        <ScrollArea className="flex-1 py-4">
          <nav className="px-3 space-y-1" aria-label="Main Navigation">
            {navItems.map((item) => {
              const isActive = currentView === item.id
              return (
                <Link
                  key={item.id}
                  to={item.href}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? "bg-secondary text-foreground font-bold shadow-sm border-l-2 border-primary"
                      : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                  }`}
                >
                  <span className={isActive ? "text-primary" : ""}>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </ScrollArea>

        {/* Sidebar Footer System Status */}
        <div className="p-3 border-t border-border/80">
          <div className="flex items-center justify-between rounded-xl bg-muted/50 p-3 border border-border/40">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <div className="flex flex-col">
                <span className="text-[11px] font-bold text-foreground leading-tight">SYSTEM ONLINE</span>
                <span className="text-[10px] text-muted-foreground leading-tight">Evidence engine active</span>
              </div>
            </div>
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/80 bg-background/95 backdrop-blur-md px-4 sm:px-6">
          {/* Left Title & Mobile Menu Button */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden h-9 w-9"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle Mobile Menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
            <h1 className="font-heading text-lg font-bold text-foreground">
              {navItems.find((n) => n.id === currentView)?.label}
            </h1>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold bg-primary/5 text-primary border-primary/20">
              <FileText className="h-3.5 w-3.5" />
              <span>{documents.length} Docs</span>
            </Badge>

            {/* Dark/Light Switcher */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-border/60 bg-card/60">
              <Sun className={`h-3.5 w-3.5 ${theme === "light" ? "text-amber-500" : "text-muted-foreground"}`} />
              <Switch checked={theme === "dark"} onCheckedChange={toggle} aria-label="Toggle dark mode" className="scale-75" />
              <Moon className={`h-3.5 w-3.5 ${theme === "dark" ? "text-blue-400" : "text-muted-foreground"}`} />
            </div>

            {/* User Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" aria-label="User account menu" className="h-9 px-3 gap-2 rounded-xl border-border/80 hover:bg-accent/60">
                  <Avatar className="h-6 w-6">
                    <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${user.name}`} alt={user.name} />
                    <AvatarFallback className="bg-primary/20 text-primary font-bold text-[10px]">{user.name?.charAt(0) || "U"}</AvatarFallback>
                  </Avatar>
                  <span className="text-xs font-semibold text-foreground hidden sm:inline">{user.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56 glass-panel" align="end" forceMount>
                <DropdownMenuLabel className="font-heading font-bold text-sm">{user.name}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-xs text-muted-foreground cursor-default">
                  <span>{user.role}</span> · <span>{user.department}</span>
                </DropdownMenuItem>
                <DropdownMenuItem className="text-xs text-muted-foreground cursor-default">
                  Jurisdiction: <span className="font-semibold text-foreground ml-1">{user.jurisdiction}</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive cursor-pointer">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Mobile Navigation Menu Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Mobile navigation menu"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="md:hidden border-b border-border/80 bg-background/95 backdrop-blur-lg px-4 py-3"
            >
              <nav className="flex flex-col gap-1.5">
                {navItems.map((item) => (
                  <Link
                    key={item.id}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                      currentView === item.id
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    }`}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </Link>
                ))}
              </nav>
            </motion.div>
          )}
        </AnimatePresence>

        {/* View Page Content */}
        <main id="main-content" className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentView}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="max-w-6xl mx-auto"
            >
              {currentView === "upload" && <UploadView onUploadComplete={loadDocuments} />}
              {currentView === "xray" && <DocumentXRay documents={documents} />}
              {currentView === "compare" && <ContractCompare documents={documents} />}
              {currentView === "brief" && <LawyerBrief documents={documents} />}
              {currentView === "chat" && <LegalChat />}
              {currentView === "glossary" && <LegalGlossary />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}