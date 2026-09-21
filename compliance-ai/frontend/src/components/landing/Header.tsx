"use client"

import { motion, useScroll, useTransform } from "framer-motion"
import { Shield, Menu, X, Sun, Moon } from "lucide-react"
import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/hooks"

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)
  const { theme, toggle } = useTheme()

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <motion.header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? "bg-background/80 backdrop-blur-md border-b border-border" : "bg-transparent border-transparent"
      }`}
    >
      <nav className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between" aria-label="Main navigation">
        <Link to="/" className="flex items-center gap-2" aria-label="LegalLens Home">
          <Shield className="h-8 w-8 text-primary" />
          <span className="font-display text-xl font-bold text-foreground">LegalLens</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link to="#features" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
            Features
          </Link>
          <Link to="#how-it-works" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
            How It Works
          </Link>
          <Link to="#security" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
            Security
          </Link>
          <Link to="/login">
            <Button variant="ghost" size="sm">
              Sign In
            </Button>
          </Link>
          <Link to="/login">
            <Button size="sm" className="gap-2">
              Start Free
              <span className="hidden sm:inline">Analysis</span>
            </Button>
          </Link>
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
            {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </Button>
        </div>
      </nav>

      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="md:hidden border-t border-border bg-background px-6 py-4"
        >
          <div className="flex flex-col gap-4">
            <Link to="#features" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2">
              Features
            </Link>
            <Link to="#how-it-works" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2">
              How It Works
            </Link>
            <Link to="#security" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2">
              Security
            </Link>
            <div className="flex flex-col gap-2 pt-2">
              <Link to="/login">
                <Button variant="outline" className="w-full justify-start">
                  Sign In
                </Button>
              </Link>
              <Link to="/login">
                <Button className="w-full justify-start">
                  Start Free Analysis
                </Button>
              </Link>
            </div>
          </div>
        </motion.div>
      )}
    </motion.header>
  )
}