"use client"

import { useState, useCallback, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Search,
  GitCompare,
  FileSearch,
  Code,
  FileSpreadsheet,
  ArrowRight,
  Layers
} from "lucide-react"
import { Link } from "react-router-dom"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { cn } from "@/lib/utils"

interface UploadViewProps {
  onUploadComplete: () => void
}

interface UploadStatusItem {
  filename: string
  status: "pending" | "uploading" | "success" | "error"
  chunks?: number
  error?: string
}

export function UploadView({ onUploadComplete }: UploadViewProps) {
  const [uploading, setUploading] = useState(false)
  const [items, setItems] = useState<UploadStatusItem[]>([])
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleUploadFiles = useCallback(
    async (files: File[]) => {
      if (!files || files.length === 0) return

      setUploading(true)
      const initialItems: UploadStatusItem[] = files.map((f) => ({
        filename: f.name,
        status: "uploading",
      }))
      setItems((prev) => [...initialItems, ...prev])

      for (const file of files) {
        try {
          console.time(`⏱️ [FE-PERF] Upload: ${file.name}`)
          console.log(`%c⏱️ [FE-PERF] Starting upload for file: ${file.name} (${file.size} bytes)`, "color: #38bdf8; font-weight: bold;")
          const t0 = performance.now()
          const res = await api.documents.upload(file)
          const dt = performance.now() - t0
          console.log(
            `%c⏱️ [FE-PERF] Finished upload for ${file.name} in ${dt.toFixed(1)}ms (${(dt / 1000).toFixed(2)}s) -> Chunks: ${res.chunks_indexed}`,
            "color: #4ade80; font-weight: bold;"
          )
          console.timeEnd(`⏱️ [FE-PERF] Upload: ${file.name}`)

          setItems((prev) =>
            prev.map((item) =>
              item.filename === file.name
                ? { ...item, status: "success", chunks: res.chunks_indexed ?? 0 }
                : item
            )
          )
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : String(err)
          console.error(`⏱️ [FE-PERF] Upload failed for ${file.name}:`, err)
          setItems((prev) =>
            prev.map((item) =>
              item.filename === file.name
                ? { ...item, status: "error", error: msg || "Upload failed" }
                : item
            )
          )
        }
      }

      setUploading(false)
      onUploadComplete()
    },
    [onUploadComplete]
  )

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleUploadFiles(Array.from(e.dataTransfer.files))
      }
    },
    [handleUploadFiles]
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        handleUploadFiles(Array.from(e.target.files))
      }
    },
    [handleUploadFiles]
  )

  return (
    <div className="space-y-10 max-w-5xl mx-auto py-4">
      {/* Hero Header */}
      <ScrollReveal className="text-center max-w-3xl mx-auto space-y-3">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.05, type: "spring", stiffness: 200 }}
          className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 text-primary shadow-glow"
        >
          <FileText className="h-8 w-8" />
        </motion.div>
        <h1 className="font-heading text-3xl sm:text-4xl md:text-5xl font-extrabold text-foreground tracking-tight text-balance">
          Upload Documents to{" "}
          <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-amber-300 bg-clip-text text-transparent">
            Start Analyzing
          </span>
        </h1>
        <p className="text-sm sm:text-base text-muted-foreground leading-relaxed max-w-2xl mx-auto">
          Drop single or multiple contracts, agreements, or legal notices below. LegalLens parses
          clauses, flags risk levels, extracts obligations, and compiles lawyer-ready briefs.
        </p>
      </ScrollReveal>

      {/* Screen Reader Live Status Region */}
      <div role="status" aria-live="polite" className="sr-only">
        {uploading && "Uploading and indexing documents, please wait..."}
      </div>

      {/* Multi-File Upload Drop Zone */}
      <ScrollReveal delay={0.1}>
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          role="region"
          aria-label="Document upload area"
          className={cn(
            "relative rounded-2xl border-2 border-dashed p-8 md:p-12 transition-all duration-300 glass-panel text-center",
            dragActive
              ? "border-primary bg-primary/10 shadow-glow"
              : "border-border/80 hover:border-primary/50 hover:shadow-lg"
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileSelect}
            disabled={uploading}
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer block w-full">
            <div className="flex flex-col items-center justify-center py-4">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20">
                <Upload className="h-8 w-8" />
              </div>
              <h3 className="font-heading text-lg sm:text-xl font-bold text-foreground mb-1">
                Drop your document(s) here or click to browse
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground mb-6">
                Supports Multi-File Selection · PDF, DOCX, TXT, or Markdown · Up to 50MB
              </p>
              <Button
                variant="default"
                size="lg"
                aria-label={uploading ? "Uploading documents" : "Choose files to upload"}
                className="gap-2 font-semibold shadow-sm hover:scale-[1.02] transition-transform"
                disabled={uploading}
              >
                <Upload className="h-4 w-4" />
                <span>{uploading ? "Uploading Batch..." : "Choose File(s)"}</span>
              </Button>
            </div>
          </label>
        </div>
      </ScrollReveal>

      {/* Uploaded Items Batch Queue Feedback */}
      <AnimatePresence>
        {items.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between px-1">
              <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-primary" />
                <span>Uploaded Documents Batch ({items.length})</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {items.map((item, idx) => (
                <Card
                  key={`${item.filename}-${idx}`}
                  className="glass-panel p-3.5 border-border/80 flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-foreground truncate">{item.filename}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {item.status === "uploading" && "Indexing vectors..."}
                        {item.status === "success" && `${item.chunks ?? 0} chunks indexed`}
                        {item.status === "error" && (item.error || "Failed")}
                      </p>
                    </div>
                  </div>

                  <div className="shrink-0">
                    {item.status === "uploading" && (
                      <svg className="h-4 w-4 animate-spin text-primary" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                    )}
                    {item.status === "success" && (
                      <Badge variant="default" className="gap-1 text-[10px] bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                        <CheckCircle2 className="h-3 w-3" /> Ready
                      </Badge>
                    )}
                    {item.status === "error" && (
                      <Badge variant="destructive" className="gap-1 text-[10px]">
                        <AlertCircle className="h-3 w-3" /> Failed
                      </Badge>
                    )}
                  </div>
                </Card>
              ))}
            </div>

            {/* Quick Actions Bar after uploading */}
            <div className="flex flex-wrap items-center justify-end gap-2 pt-2">
              <Button asChild variant="outline" size="sm" className="h-8 text-xs gap-1.5 rounded-xl">
                <Link to="/app/xray">
                  <span>Run Document X-Ray</span>
                  <ArrowRight className="h-3.5 w-3.5 text-primary" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="sm" className="h-8 text-xs gap-1.5 rounded-xl">
                <Link to="/app/compare">
                  <span>Compare Contracts</span>
                  <ArrowRight className="h-3.5 w-3.5 text-primary" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="sm" className="h-8 text-xs gap-1.5 rounded-xl">
                <Link to="/app/brief">
                  <span>Generate Brief</span>
                  <ArrowRight className="h-3.5 w-3.5 text-primary" />
                </Link>
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Format Badges Grid */}
      <ScrollReveal delay={0.15}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { icon: FileText, label: "PDF Document", desc: "Contracts & Agreements" },
            { icon: FileSpreadsheet, label: "DOCX Format", desc: "Word Documents" },
            { icon: FileText, label: "TXT File", desc: "Plain Text Data" },
            { icon: Code, label: "Markdown", desc: "Structured MD Docs" },
          ].map((format) => (
            <Card key={format.label} className="glass-panel p-4 text-center hover:border-primary/40 transition-all">
              <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <format.icon className="h-5 w-5" />
              </div>
              <p className="font-heading font-bold text-sm text-foreground">{format.label}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">{format.desc}</p>
            </Card>
          ))}
        </div>
      </ScrollReveal>

      {/* Feature Capabilities Grid */}
      <StaggerContainer staggerDelay={0.1} className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        {[
          { icon: Search, title: "Document X-Ray", desc: "Clause-level risk analysis, obligations, and section citations", accent: "hover:border-blue-500/40" },
          { icon: GitCompare, title: "Contract Compare", desc: "Side-by-side clause diffs with plain-English impact rationale", accent: "hover:border-amber-500/40" },
          { icon: FileSearch, title: "Lawyer Brief", desc: "Actionable pre-consultation package for your legal counsel", accent: "hover:border-purple-500/40" },
        ].map((feature) => (
          <StaggerItem key={feature.title} direction="up">
            <Card className={`h-full glass-panel p-6 text-center transition-all ${feature.accent}`}>
              <CardContent className="p-0 flex flex-col items-center justify-between h-full space-y-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <feature.icon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-heading text-lg font-bold text-foreground mb-1">{feature.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{feature.desc}</p>
                </div>
              </CardContent>
            </Card>
          </StaggerItem>
        ))}
      </StaggerContainer>
    </div>
  )
}