"use client"

import { motion } from "framer-motion"
import { Shield, ArrowRight, FileText, Search, Scale, Sparkles, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { Link } from "react-router-dom"

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden py-16 md:py-24">
      {/* ReactBits Radial Glow Background */}
      <div className="absolute inset-0 -z-10 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-gradient-to-tr from-blue-600/20 via-purple-600/15 to-amber-500/10 blur-[130px] rounded-full animate-pulse-glow" />
        <div className="absolute top-1/2 left-1/3 w-[350px] h-[350px] bg-blue-500/10 blur-[100px] rounded-full" />
      </div>

      <div className="relative z-10 px-6 max-w-7xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="text-center max-w-4xl mx-auto"
        >
          {/* Animated Badge */}
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs md:text-sm font-semibold mb-8 backdrop-blur-md shadow-sm"
          >
            <Sparkles className="h-4 w-4 text-amber-400 animate-spin-slow" />
            <span>AI Legal Document Intelligence Platform</span>
            <Badge variant="secondary" className="ml-1 text-[10px] px-1.5 py-0 bg-primary/20 text-primary border-none">
              v2.0
            </Badge>
          </motion.div>

          {/* Main Title */}
          <h1 className="font-heading text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold text-foreground tracking-tight leading-[1.08] mb-6 text-balance">
            Evidence-First AI for{" "}
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-amber-300 bg-clip-text text-transparent">
              Understanding Legal Documents
            </span>
          </h1>

          {/* Description */}
          <p className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
            Upload contracts, agreements, or notices. LegalLens provides instant <strong className="text-foreground font-semibold">Document X-Ray</strong> analysis, clause extraction, obligations, and contract comparisons — backed by direct source citations.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Button size="xl" className="w-full sm:w-auto gap-2 text-base font-semibold shadow-glow transition-all hover:scale-[1.02]" asChild>
              <Link to="/login">
                <span>Start Analyzing Document</span>
                <ArrowRight className="h-5 w-5" />
              </Link>
            </Button>
            <Button variant="outline" size="xl" className="w-full sm:w-auto gap-2 text-base font-semibold glass-panel hover:bg-accent/80 transition-all" asChild>
              <Link to="/login">
                <FileText className="h-5 w-5 text-amber-400" />
                <span>Try Sample Contracts</span>
              </Link>
            </Button>
          </div>

          {/* Trust Highlights */}
          <div className="flex flex-wrap items-center justify-center gap-6 md:gap-10 text-xs sm:text-sm text-muted-foreground pt-4 border-t border-border/40">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-emerald-400" />
              <span className="font-medium text-foreground/80">Instruction Injection Guard</span>
            </div>
            <div className="flex items-center gap-2">
              <Scale className="h-4 w-4 text-blue-400" />
              <span className="font-medium text-foreground/80">Jurisdiction Precedence</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-amber-400" />
              <span className="font-medium text-foreground/80">Citation-Grounded Engine</span>
            </div>
          </div>
        </motion.div>

        {/* Feature Cards Grid */}
        <StaggerContainer staggerDelay={0.12} className="mt-16 sm:mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <StaggerItem direction="up">
            <Card className="group relative overflow-hidden glass-panel hover:border-primary/40 hover:shadow-glow transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 mb-4 group-hover:bg-blue-500 group-hover:text-white transition-colors duration-300">
                  <FileText className="h-6 w-6" />
                </div>
                <h3 className="font-heading text-xl font-bold text-foreground mb-2">Document X-Ray</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Deep clause analysis, severity risk flags (🔴/🟡/🟢), extracted obligations, and plain-English summaries.
                </p>
              </CardContent>
            </Card>
          </StaggerItem>

          <StaggerItem direction="up">
            <Card className="group relative overflow-hidden glass-panel hover:border-amber-500/40 hover:shadow-glow-amber transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 mb-4 group-hover:bg-amber-500 group-hover:text-white transition-colors duration-300">
                  <Search className="h-6 w-6" />
                </div>
                <h3 className="font-heading text-xl font-bold text-foreground mb-2">Contract Compare</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Side-by-side clause comparison highlighting modified notice periods, non-competes, and liability caps with impact analysis.
                </p>
              </CardContent>
            </Card>
          </StaggerItem>

          <StaggerItem direction="up">
            <Card className="group relative overflow-hidden glass-panel hover:border-purple-500/40 hover:shadow-glow transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 mb-4 group-hover:bg-purple-500 group-hover:text-white transition-colors duration-300">
                  <Scale className="h-6 w-6" />
                </div>
                <h3 className="font-heading text-xl font-bold text-foreground mb-2">Lawyer Brief</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Actionable pre-consultation packages with key risk areas, checklist items, and formulated questions for legal counsel.
                </p>
              </CardContent>
            </Card>
          </StaggerItem>
        </StaggerContainer>
      </div>
    </section>
  )
}