"use client"

import { Shield, FileSearch, GitCompare, MessageSquare, CheckCircle2, Zap, Brain } from "lucide-react"
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const features = [
  {
    icon: FileSearch,
    title: "Document X-Ray Analysis",
    description:
      "Upload any legal document and get a comprehensive breakdown of key clauses, risk levels, obligations, and deadlines — all with precise source citations.",
    highlights: ["Clause classification", "Risk scoring (HIGH/MEDIUM/LOW)", "Obligation extraction", "Lawyer-ready questions"],
    accent: "border-blue-500/20 hover:border-blue-500/40 hover:shadow-glow",
  },
  {
    icon: GitCompare,
    title: "Contract Comparison",
    description:
      "Compare two versions or different contracts side by side. See exactly what changed, what stayed the same, and why each change matters.",
    highlights: ["Side-by-side diff view", "Change impact analysis", "Clause-level granularity", "Version-aware"],
    accent: "border-amber-500/20 hover:border-amber-500/40 hover:shadow-glow-amber",
  },
  {
    icon: Brain,
    title: "Lawyer Brief Generation",
    description:
      "Generate a pre-consultation brief for your attorney: situation summary, key clauses to discuss, risk areas, recommended questions, and documents to gather.",
    highlights: ["Situation summary", "Risk area identification", "Recommended questions", "Information checklist"],
    accent: "border-purple-500/20 hover:border-purple-500/40 hover:shadow-glow",
  },
  {
    icon: MessageSquare,
    title: "Legal Q&A Chat",
    description:
      "Ask questions about your documents and get grounded answers with evidence assessment. Every answer cites sources and shows its confidence level.",
    highlights: ["Evidence-grounded answers", "Citation cards", "Decision badges", "Conflict detection"],
    accent: "border-emerald-500/20 hover:border-emerald-500/40 hover:shadow-glow",
  },
  {
    icon: Shield,
    title: "Security & Guardrails",
    description:
      "Built with strict document-level prompt injection protection. Uploaded contracts are parsed purely as evidence, never executable instructions.",
    highlights: ["Instruction injection guard", "Jurisdiction precedence", "Audit logging", "Data privacy"],
    accent: "border-indigo-500/20 hover:border-indigo-500/40 hover:shadow-glow",
  },
  {
    icon: Zap,
    title: "Sub-Second Analysis",
    description:
      "No training required. Upload and analyze in seconds. Works with PDFs, Word docs, and plain text across multiple jurisdictions.",
    highlights: ["Sub-second analysis", "Multi-format support", "Multi-jurisdiction", "Offline-capable"],
    accent: "border-cyan-500/20 hover:border-cyan-500/40 hover:shadow-glow",
  },
]

export function Features() {
  return (
    <section className="py-24 md:py-32 px-6 bg-background relative overflow-hidden">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="outline" className="mb-4 px-3 py-1 text-xs font-semibold text-primary border-primary/30">
            Comprehensive Capabilities
          </Badge>
          <h2 className="font-heading text-3xl sm:text-4xl md:text-5xl font-extrabold text-foreground tracking-tight mb-4 text-balance">
            Built for{" "}
            <span className="bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">
              Individuals & Legal Teams
            </span>
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            Every feature is designed to save hours of manual review — while keeping exact contract text and human judgment at the center.
          </p>
        </ScrollReveal>

        <StaggerContainer staggerDelay={0.08} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <StaggerItem key={feature.title} direction="up">
              <FeatureCard feature={feature} />
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  )
}

function FeatureCard({ feature }: { feature: typeof features[0] }) {
  return (
    <Card className={`h-full glass-panel transition-all duration-300 ${feature.accent} group`}>
      <CardHeader className="pb-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary mb-3 group-hover:bg-primary group-hover:text-white transition-colors duration-300">
          <feature.icon className="h-6 w-6" />
        </div>
        <CardTitle className="font-heading text-xl font-bold text-foreground">
          {feature.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
        <ul className="space-y-2 pt-2 border-t border-border/40">
          {feature.highlights.map((highlight, i) => (
            <li key={i} className="flex items-center gap-2 text-xs font-medium text-foreground/80">
              <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0" />
              <span>{highlight}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}