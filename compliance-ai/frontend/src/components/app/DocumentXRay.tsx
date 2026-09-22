"use client"

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, ChevronDown, ChevronUp, AlertTriangle, CheckCircle2, AlertCircle, HelpCircle, Scale } from "lucide-react"
import { api, type XRayResult, type DocumentInfo } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip"
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { LEGAL_GLOSSARY, type GlossaryTerm } from "./legalGlossaryData"
import { cn } from "@/lib/utils"

const SEVERITY_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  HIGH: { color: "text-red-500 bg-red-500/10 border-red-500/30", icon: <AlertTriangle className="h-4 w-4" />, label: "High Risk" },
  MEDIUM: { color: "text-amber-500 bg-amber-500/10 border-amber-500/30", icon: <AlertCircle className="h-4 w-4" />, label: "Review" },
  LOW: { color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/30", icon: <CheckCircle2 className="h-4 w-4" />, label: "Standard" },
}

const CLAUSE_LABELS: Record<string, string> = {
  TERMINATION: "Termination", PAYMENT: "Payment", LIABILITY: "Liability",
  INDEMNITY: "Indemnification", CONFIDENTIALITY: "Confidentiality",
  IP_ASSIGNMENT: "IP Assignment", NON_COMPETE: "Non-Compete",
  NON_SOLICITATION: "Non-Solicitation", DISPUTE_RESOLUTION: "Dispute Resolution",
  GOVERNING_LAW: "Governing Law", RENEWAL: "Renewal", WARRANTY: "Warranty",
  PRIVACY_DATA: "Privacy / Data", SCOPE_OF_WORK: "Scope of Work",
  DATA_PROCESSING: "Data Processing", OTHER: "Other",
}

interface DocumentXRayProps {
  documents: DocumentInfo[]
}

export function DocumentXRay({ documents }: DocumentXRayProps) {
  const [selectedDoc, setSelectedDoc] = useState<string>("")
  const [language, setLanguage] = useState<"en" | "hi">("en")
  const [result, setResult] = useState<XRayResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [expandedFinding, setExpandedFinding] = useState<number | null>(null)

  const analyze = useCallback(async () => {
    if (!selectedDoc) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await api.legal.xray(selectedDoc, language)
      setResult(res)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg || "Analysis failed")
    } finally {
      setLoading(false)
    }
  }, [selectedDoc, language])

  const riskConfig = result ? SEVERITY_CONFIG[result.overall_risk] || SEVERITY_CONFIG.MEDIUM : null

  return (
    <div className="space-y-6">
      {/* Screen Reader Live Announcer */}
      <div role="status" aria-live="assertive" className="sr-only">
        {loading && "Analyzing document clauses and risk levels, please wait..."}
        {result && "Document X-Ray analysis complete."}
      </div>

      {/* Header */}
      <ScrollReveal>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-foreground">Document X-Ray</h1>
            <p className="text-muted-foreground mt-1">Deep analysis of clauses, risks, and obligations</p>
          </div>
        </div>
      </ScrollReveal>

      {/* Document Selector */}
      <ScrollReveal delay={0.05}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 text-primary" aria-hidden="true" /> Select Document
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3 sm:gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium text-muted-foreground block mb-1.5" htmlFor="select-xray-doc">
                  Document to Analyze
                </label>
                <Select value={selectedDoc} onValueChange={setSelectedDoc}>
                  <SelectTrigger id="select-xray-doc" aria-label="Select document to analyze with X-Ray" className="w-full">
                    <SelectValue placeholder="Choose a document to analyze..." />
                  </SelectTrigger>
                  <SelectContent>
                    {documents.map((d) => {
                      const isUploaded = d.authority_type === "USER_DOCUMENT" || (d.source_path && d.source_path.toLowerCase().includes("uploads"))
                      return (
                        <SelectItem key={d.document_id} value={d.document_id}>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{d.title}</span>
                            <span className="text-muted-foreground font-mono text-xs">({d.document_id})</span>
                            <Badge variant={isUploaded ? "default" : "outline"} className="text-xs px-1.5 py-0 ml-auto shrink-0">
                              {isUploaded ? "UPLOADED" : "DEMO"}
                            </Badge>
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>

              {/* Vernacular Language Selector */}
              <div className="w-full sm:w-44 shrink-0">
                <label className="text-sm font-medium text-muted-foreground block mb-1.5" htmlFor="select-xray-lang">
                  Language
                </label>
                <Select value={language} onValueChange={(val: "en" | "hi") => setLanguage(val)}>
                  <SelectTrigger id="select-xray-lang" aria-label="Select analysis language" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English (Default)</SelectItem>
                    <SelectItem value="hi">Hindi (हिन्दी)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={analyze} disabled={!selectedDoc || loading} aria-label="Run Document X-Ray analysis" className="gap-2 shrink-0">
                {loading ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" aria-hidden="true" /> Analyze Document
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </ScrollReveal>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="rounded-lg border border-destructive/30 bg-destructive/5 p-4"
          >
            <p className="text-sm text-destructive">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Risk Summary */}
            <ScrollReveal>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className={cn("flex h-16 w-16 shrink-0 items-center justify-center rounded-xl text-2xl", riskConfig?.color)}>
                      {riskConfig?.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h2 className="font-display text-2xl font-bold text-foreground">{result.title}</h2>
                        <Badge variant={result.overall_risk === "HIGH" ? "destructive" : result.overall_risk === "MEDIUM" ? "default" : "secondary"}>
                          {riskConfig?.label}
                        </Badge>
                      </div>
                      <p className="mt-2 text-muted-foreground leading-relaxed">{result.summary}</p>
                      <div className="mt-4 flex flex-wrap gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1"><Scale className="h-4 w-4" /> {result.findings.length} findings</span>
                        <span className="flex items-center gap-1"><HelpCircle className="h-4 w-4" /> {result.obligations.length} obligations</span>
                        <span className="flex items-center gap-1"><AlertTriangle className="h-4 w-4" /> {result.lawyer_questions.length} questions</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </ScrollReveal>

            {/* Key Findings */}
            <ScrollReveal delay={0.05}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">Key Findings</CardTitle>
                </CardHeader>
                <CardContent>
                  <StaggerContainer staggerDelay={0.05}>
                    {result.findings.map((f, i) => {
                      const sev = SEVERITY_CONFIG[f.severity] || SEVERITY_CONFIG.MEDIUM
                      const isExpanded = expandedFinding === i
                      return (
                        <StaggerItem key={i} direction="up">
                          <div
                            className={cn(
                              "rounded-xl border transition-colors hover:bg-accent/50",
                              isExpanded && "bg-accent/30"
                            )}
                          >
                            <button
                              type="button"
                              onClick={() => setExpandedFinding(isExpanded ? null : i)}
                              aria-expanded={isExpanded}
                              aria-controls={`finding-details-${i}`}
                              id={`finding-btn-${i}`}
                              className="w-full text-left p-4 flex items-start gap-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-xl"
                            >
                              <div className={cn("mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full", sev.color)}>
                                {sev.icon}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="font-semibold text-foreground">{f.title}</span>
                                  {(() => {
                                    const label = CLAUSE_LABELS[f.clause_type] || f.clause_type
                                    const glossaryMatch = LEGAL_GLOSSARY.find(
                                      (g: GlossaryTerm) =>
                                        g.term.toLowerCase().includes(label.toLowerCase()) ||
                                        label.toLowerCase().includes(g.term.toLowerCase()) ||
                                        f.title.toLowerCase().includes(g.term.toLowerCase())
                                    )
                                    return (
                                      <TooltipProvider>
                                        <Tooltip>
                                          <TooltipTrigger asChild>
                                            <span tabIndex={0} role="button" aria-label={`Glossary definition for ${label}`}>
                                              <Badge
                                                variant={f.severity === "HIGH" ? "destructive" : f.severity === "MEDIUM" ? "default" : "secondary"}
                                                className="cursor-help"
                                              >
                                                {label}
                                              </Badge>
                                            </span>
                                          </TooltipTrigger>
                                          <TooltipContent className="max-w-xs text-xs space-y-1 p-3 glass-panel">
                                            <p className="font-bold text-foreground">{glossaryMatch?.term || label}</p>
                                            <p className="text-muted-foreground">{glossaryMatch?.plainEnglish || f.explanation}</p>
                                            {glossaryMatch?.whyItMatters && (
                                              <p className="text-primary font-medium">{glossaryMatch.whyItMatters}</p>
                                            )}
                                          </TooltipContent>
                                        </Tooltip>
                                      </TooltipProvider>
                                    )
                                  })()}
                                  <span className="text-xs text-muted-foreground font-mono">{f.section}</span>
                                </div>
                                <p className="mt-1 text-sm text-muted-foreground">{f.explanation}</p>
                              </div>
                              {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0 mt-1" /> : <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />}
                            </button>

                            <AnimatePresence>
                              {isExpanded && (
                                <motion.div
                                  id={`finding-details-${i}`}
                                  role="region"
                                  aria-labelledby={`finding-btn-${i}`}
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  transition={{ duration: 0.2 }}
                                  className="overflow-hidden px-4 pb-4 space-y-3 border-t pt-3"
                                >
                                  <div>
                                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Original Clause</h4>
                                    <p className="text-xs text-foreground bg-muted rounded-lg p-3 font-mono whitespace-pre-wrap">{f.source_text}</p>
                                  </div>
                                  <div>
                                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Why This Matters</h4>
                                    <p className="text-sm text-foreground">{f.why_it_matters}</p>
                                  </div>
                                  <div className="rounded-lg border border-primary/30 bg-primary/5 p-3">
                                    <h4 className="text-xs font-semibold uppercase tracking-wider text-primary mb-1">Question for a Lawyer</h4>
                                    <p className="text-sm text-foreground">{f.lawyer_question}</p>
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        </StaggerItem>
                      )
                    })}
                  </StaggerContainer>
                </CardContent>
              </Card>
            </ScrollReveal>

            {/* Obligations */}
            {result.obligations.length > 0 && (
              <ScrollReveal delay={0.1}>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">Obligations & Deadlines</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <StaggerContainer staggerDelay={0.05}>
                      {result.obligations.map((o, i) => (
                        <StaggerItem key={i} direction="up">
                          <div className="rounded-xl border p-4">
                            <div className="flex items-start gap-3">
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary text-sm font-bold">
                                {i + 1}
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <Badge variant="outline">{o.subject}</Badge>
                                  <span className="text-sm font-medium text-foreground">{o.action}</span>
                                </div>
                                <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-muted-foreground">
                                  <div><span className="font-semibold">Deadline:</span> {o.deadline}</div>
                                  <div><span className="font-semibold">Condition:</span> {o.condition}</div>
                                  <div><span className="font-semibold">Source:</span> <span className="font-mono">{o.source_section}</span></div>
                                </div>
                                {o.consequence && (
                                  <p className="mt-2 text-xs text-amber-500 flex items-center gap-1">
                                    <AlertTriangle className="h-3 w-3" /> {o.consequence}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        </StaggerItem>
                      ))}
                    </StaggerContainer>
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}

            {/* Lawyer Questions */}
            {result.lawyer_questions.length > 0 && (
              <ScrollReveal delay={0.15}>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">Questions for a Lawyer</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <StaggerContainer staggerDelay={0.03}>
                      {result.lawyer_questions.map((q, i) => (
                        <StaggerItem key={i} direction="up">
                          <div className="flex items-start gap-3 rounded-xl border p-3">
                            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                              <HelpCircle className="h-3 w-3" />
                            </div>
                            <p className="text-sm text-foreground">{q}</p>
                          </div>
                        </StaggerItem>
                      ))}
                    </StaggerContainer>
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}

            {/* Disclaimer */}
            <ScrollReveal delay={0.2}>
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-xs text-muted-foreground">
                <strong className="text-amber-500">Information, not legal advice.</strong> This analysis explains the provided documents and identifies issues for review. It does not determine legal rights or guarantee enforceability. Consult a qualified legal professional for advice.
              </div>
            </ScrollReveal>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}