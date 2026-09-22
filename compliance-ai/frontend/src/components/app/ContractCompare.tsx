"use client"

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { GitCompare, AlertTriangle, CheckCircle2, Plus, Minus } from "lucide-react"
import { api, type CompareResult, type DocumentInfo } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { cn } from "@/lib/utils"

const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode }> = {
  CHANGED: { color: "text-red-500 bg-red-500/10 border-red-500/30", icon: <AlertTriangle className="h-4 w-4" /> },
  ADDED: { color: "text-blue-500 bg-blue-500/10 border-blue-500/30", icon: <Plus className="h-4 w-4" /> },
  REMOVED: { color: "text-zinc-500 bg-zinc-500/10 border-zinc-500/30", icon: <Minus className="h-4 w-4" /> },
  SAME: { color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/30", icon: <CheckCircle2 className="h-4 w-4" /> },
}

const CLAUSE_LABELS: Record<string, string> = {
  TERMINATION: "Termination", PAYMENT: "Payment", LIABILITY: "Liability",
  INDEMNITY: "Indemnification", CONFIDENTIALITY: "Confidentiality",
  IP_ASSIGNMENT: "IP Assignment", NON_COMPETE: "Non-Compete",
  NON_SOLICITATION: "Non-Solicitation", DISPUTE_RESOLUTION: "Dispute Resolution",
  GOVERNING_LAW: "Governing Law", RENEWAL: "Renewal", SCOPE_OF_WORK: "Scope of Work",
  DATA_PROCESSING: "Data Processing", OTHER: "Other",
}

interface ContractCompareProps {
  documents: DocumentInfo[]
}

export function ContractCompare({ documents }: ContractCompareProps) {
  const [docA, setDocA] = useState("")
  const [docB, setDocB] = useState("")
  const [result, setResult] = useState<CompareResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const compare = useCallback(async () => {
    if (!docA || !docB) return
    if (docA === docB) {
      setError("Please select two different documents to compare.")
      return
    }
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await api.legal.compare(docA, docB)
      setResult(res)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg || "Comparison failed")
    } finally {
      setLoading(false)
    }
  }, [docA, docB])

  const changedCount = result?.comparisons.filter((c) => c.status === "CHANGED").length || 0
  const sameCount = result?.comparisons.filter((c) => c.status === "SAME").length || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <ScrollReveal>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-foreground">Contract Compare</h1>
            <p className="text-muted-foreground mt-1">Side-by-side clause comparison with impact analysis</p>
          </div>
        </div>
      </ScrollReveal>

      {/* Document Selectors */}
      <ScrollReveal delay={0.05}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitCompare className="h-5 w-5 text-primary" /> Select Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground" htmlFor="select-doc-a">Document A</label>
                <Select value={docA} onValueChange={setDocA}>
                  <SelectTrigger id="select-doc-a" className="mt-1 w-full" aria-label="Select first document to compare">
                    <SelectValue placeholder="Select first document..." />
                  </SelectTrigger>
                  <SelectContent>
                    {documents.map((d) => {
                      const isUploaded = d.authority_type === "USER_DOCUMENT" || (d.source_path && d.source_path.toLowerCase().includes("uploads"))
                      return (
                        <SelectItem key={d.document_id} value={d.document_id}>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{d.title}</span>
                            <span className="text-muted-foreground font-mono text-[10px]">({d.document_id})</span>
                            <Badge variant={isUploaded ? "default" : "outline"} className="text-[9px] px-1.5 py-0 ml-auto shrink-0">
                              {isUploaded ? "UPLOADED" : "DEMO"}
                            </Badge>
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground" htmlFor="select-doc-b">Document B</label>
                <Select value={docB} onValueChange={setDocB}>
                  <SelectTrigger id="select-doc-b" className="mt-1 w-full" aria-label="Select second document to compare">
                    <SelectValue placeholder="Select second document..." />
                  </SelectTrigger>
                  <SelectContent>
                    {documents.map((d) => {
                      const isUploaded = d.authority_type === "USER_DOCUMENT" || (d.source_path && d.source_path.toLowerCase().includes("uploads"))
                      return (
                        <SelectItem key={d.document_id} value={d.document_id}>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{d.title}</span>
                            <span className="text-muted-foreground font-mono text-[10px]">({d.document_id})</span>
                            <Badge variant={isUploaded ? "default" : "outline"} className="text-[9px] px-1.5 py-0 ml-auto shrink-0">
                              {isUploaded ? "UPLOADED" : "DEMO"}
                            </Badge>
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="mt-4">
              <Button onClick={compare} disabled={!docA || !docB || loading} aria-label="Compare selected documents" className="gap-2">
                {loading ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Comparing...
                  </>
                ) : (
                  <>
                    <GitCompare className="h-4 w-4" aria-hidden="true" /> Compare Documents
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
            {/* Summary Header */}
            <ScrollReveal>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-4 flex-wrap">
                    <div className="flex-1">
                      <h2 className="font-display text-xl font-bold text-foreground">Comparison Results</h2>
                      <p className="text-sm text-muted-foreground mt-1">{result.summary}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="destructive" className="gap-1">
                        <AlertTriangle className="h-3 w-3" /> {changedCount} Changed
                      </Badge>
                      <Badge variant="secondary" className="gap-1">
                        <CheckCircle2 className="h-3 w-3" /> {sameCount} Same
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </ScrollReveal>

            {/* Clause Comparison Table */}
            <ScrollReveal delay={0.05}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">Clause-by-Clause Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <StaggerContainer staggerDelay={0.05}>
                    {result.comparisons.map((c, i) => {
                      const st = STATUS_CONFIG[c.status] || STATUS_CONFIG.SAME
                      return (
                        <StaggerItem key={i} direction="up">
                          <motion.div className="rounded-xl border overflow-hidden">
                            <div className="flex items-center gap-3 bg-muted/50 px-4 py-3">
                              <div className={cn("flex h-6 w-6 shrink-0 items-center justify-center rounded-full", st.color)}>
                                {st.icon}
                              </div>
                              <span className="font-semibold text-foreground">
                                {CLAUSE_LABELS[c.clause_type] || c.clause_type}
                              </span>
                              <Badge variant={c.status === "CHANGED" ? "destructive" : c.status === "SAME" ? "default" : "secondary"}>
                                {c.status}
                              </Badge>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x">
                              <div className="p-4">
                                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Document A</p>
                                <p className="text-sm text-foreground font-mono bg-muted/50 rounded-lg p-3 whitespace-pre-wrap">
                                  {c.document_a_text || "—"}
                                </p>
                              </div>
                              <div className="p-4">
                                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Document B</p>
                                <p className="text-sm text-foreground font-mono bg-muted/50 rounded-lg p-3 whitespace-pre-wrap">
                                  {c.document_b_text || "—"}
                                </p>
                              </div>
                            </div>

                            {c.status === "CHANGED" && c.impact && (
                              <div className="border-t bg-amber-500/5 px-4 py-3">
                                <p className="text-xs font-semibold uppercase tracking-wider text-amber-500 mb-1">Why This Change Matters</p>
                                <p className="text-sm text-foreground">{c.impact}</p>
                              </div>
                            )}
                          </motion.div>
                        </StaggerItem>
                      )
                    })}
                  </StaggerContainer>
                </CardContent>
              </Card>
            </ScrollReveal>

            {/* Disclaimer */}
            <ScrollReveal delay={0.1}>
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-xs text-muted-foreground">
                <strong className="text-amber-500">Information, not legal advice.</strong> This comparison highlights differences between documents for review purposes. It does not determine which terms are legally superior or enforceable.
              </div>
            </ScrollReveal>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}