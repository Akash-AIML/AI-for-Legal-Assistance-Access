"use client"

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FileSearch, HelpCircle, Paperclip } from "lucide-react"
import { api, type LawyerBriefResult, type DocumentInfo } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/landing/animated"

interface LawyerBriefProps {
  documents: DocumentInfo[]
}

export function LawyerBrief({ documents }: LawyerBriefProps) {
  const [selectedDoc, setSelectedDoc] = useState("")
  const [result, setResult] = useState<LawyerBriefResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const generate = useCallback(async () => {
    if (!selectedDoc) return
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await api.legal.brief(selectedDoc)
      setResult(res)
    } catch (err: any) {
      setError(err.message || "Brief generation failed")
    } finally {
      setLoading(false)
    }
  }, [selectedDoc])

  return (
    <div className="space-y-6">
      {/* Header */}
      <ScrollReveal>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display text-3xl font-bold text-foreground">Lawyer Brief</h1>
            <p className="text-muted-foreground mt-1">Pre-consultation brief with key clauses, risks, and questions</p>
          </div>
        </div>
      </ScrollReveal>

      {/* Document Selector */}
      <ScrollReveal delay={0.05}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSearch className="h-5 w-5 text-primary" /> Generate Brief
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-4">
              <div className="flex-1">
                <Select value={selectedDoc} onValueChange={setSelectedDoc}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Choose a document..." />
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
              <Button onClick={generate} disabled={!selectedDoc || loading} className="gap-2">
                {loading ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Generating...
                  </>
                ) : (
                  <>
                    <FileSearch className="h-4 w-4" /> Generate Brief
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

      {/* Brief Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Situation */}
            <ScrollReveal>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">Situation Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-foreground leading-relaxed">{result.situation}</p>
                </CardContent>
              </Card>
            </ScrollReveal>

            {/* Key Clauses */}
            {result.key_clauses.length > 0 && (
              <ScrollReveal delay={0.05}>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">Key Clauses to Discuss</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <StaggerContainer staggerDelay={0.05}>
                      {result.key_clauses.map((kc, i) => (
                        <StaggerItem key={i} direction="up">
                          <motion.div className="flex items-start gap-3 rounded-xl border p-4">
                            <Badge variant="outline">{kc.clause_type}</Badge>
                            <div className="flex-1">
                              <p className="text-xs font-mono text-muted-foreground">{kc.section}</p>
                              <p className="mt-1 text-sm text-foreground">{kc.why_it_matters}</p>
                            </div>
                          </motion.div>
                        </StaggerItem>
                      ))}
                    </StaggerContainer>
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}

            {/* Risk Areas */}
            {result.risk_areas.length > 0 && (
              <ScrollReveal delay={0.1}>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">Risk Areas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <StaggerContainer staggerDelay={0.05}>
                      {result.risk_areas.map((ra, i) => (
                        <StaggerItem key={i} direction="up">
                          <motion.div className="flex items-start gap-3 rounded-xl border p-4">
                            <Badge variant={ra.severity === "HIGH" ? "destructive" : ra.severity === "MEDIUM" ? "default" : "secondary"}>
                              {ra.severity}
                            </Badge>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-foreground">{ra.description}</p>
                              <p className="text-xs text-muted-foreground font-mono">{ra.source}</p>
                            </div>
                          </motion.div>
                        </StaggerItem>
                      ))}
                    </StaggerContainer>
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}

            {/* Recommended Questions */}
            <ScrollReveal delay={0.15}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">Recommended Questions for Your Lawyer</CardTitle>
                </CardHeader>
                <CardContent>
                  <StaggerContainer staggerDelay={0.03}>
                    {result.recommended_questions.map((q, i) => (
                      <StaggerItem key={i} direction="up">
                        <motion.div className="flex items-start gap-3 rounded-xl border p-3">
                          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                            <HelpCircle className="h-3 w-3" />
                          </div>
                          <p className="text-sm text-foreground">{q}</p>
                        </motion.div>
                      </StaggerItem>
                    ))}
                  </StaggerContainer>
                </CardContent>
              </Card>
            </ScrollReveal>

            {/* Information to Gather */}
            {result.information_to_gather.length > 0 && (
              <ScrollReveal delay={0.2}>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">Information to Gather Before Your Consultation</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <StaggerContainer staggerDelay={0.03}>
                      {result.information_to_gather.map((item, i) => (
                        <StaggerItem key={i} direction="up">
                          <motion.div className="flex items-start gap-3 rounded-xl border p-3">
                            <Paperclip className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                            <p className="text-sm text-foreground">{item}</p>
                          </motion.div>
                        </StaggerItem>
                      ))}
                    </StaggerContainer>
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}

            {/* Disclaimer */}
            <ScrollReveal delay={0.25}>
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-xs text-muted-foreground">
                <strong className="text-amber-500">Information, not legal advice.</strong> This brief is prepared for discussion purposes only. It does not constitute legal advice or create an attorney-client relationship.
              </div>
            </ScrollReveal>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}