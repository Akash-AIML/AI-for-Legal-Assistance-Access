"use client"

import { useState } from "react"
import { BookOpen, Search } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export interface GlossaryTerm {
  term: string
  plainEnglish: string
  whyItMatters: string
  category: "Risk" | "Obligation" | "Standard" | "Financial"
}

export const LEGAL_GLOSSARY: GlossaryTerm[] = [
  {
    term: "Indemnification",
    plainEnglish: "An agreement where one party promises to compensate and cover legal fees or damages suffered by the other party.",
    whyItMatters: "High risk: You could be forced to pay thousands in legal costs even if you were only partly at fault.",
    category: "Risk",
  },
  {
    term: "Limitation of Liability",
    plainEnglish: "A clause that sets a maximum dollar cap on the amount of damages one party can recover from the other in a dispute.",
    whyItMatters: "Protective for providers, but can severely limit your financial recovery if you suffer significant losses.",
    category: "Risk",
  },
  {
    term: "Liquidated Damages",
    plainEnglish: "A predetermined, fixed sum of money specified in the contract that must be paid if a specific breach occurs.",
    whyItMatters: "Avoids court estimation of damages, but can be punitive if the set sum is disproportionate to actual harm.",
    category: "Financial",
  },
  {
    term: "Severability",
    plainEnglish: "Ensures that if one clause is found invalid or unenforceable by a court, the remainder of the agreement remains valid.",
    whyItMatters: "Prevents an entire agreement from being cancelled because of a single flawed paragraph.",
    category: "Standard",
  },
  {
    term: "Governing Law & Jurisdiction",
    plainEnglish: "Specifies which state's or country's laws control the agreement and which court has authority to resolve disputes.",
    whyItMatters: "Could force you to travel to another state or country to defend yourself in court.",
    category: "Standard",
  },
  {
    term: "Non-Compete Clause",
    plainEnglish: "Restricts you from working for competitors or starting a similar competing business for a specified duration and geography.",
    whyItMatters: "High risk for employees and freelancers: Can prevent you from earning a livelihood after leaving.",
    category: "Risk",
  },
  {
    term: "Force Majeure",
    plainEnglish: "Frees parties from liability or contractual obligations when an extraordinary event beyond control occurs (e.g. natural disasters, war).",
    whyItMatters: "Protects against breaches caused by unforeseen catastrophes, but must explicitly list the qualifying events.",
    category: "Standard",
  },
  {
    term: "Automatic Renewal (Evergreen)",
    plainEnglish: "A provision where the contract automatically renews for another term unless written cancellation is provided within a specific window.",
    whyItMatters: "Can lock you into unwanted contracts and payments if you miss the narrow cancellation deadline.",
    category: "Obligation",
  },
  {
    term: "Arbitration Clause",
    plainEnglish: "Mandates that disputes be resolved by a private arbitrator rather than through a public judge and jury court trial.",
    whyItMatters: "Waives your right to a court trial and appeal; arbitration proceedings are often confidential and costly.",
    category: "Risk",
  },
  {
    term: "Notice Period",
    plainEnglish: "The minimum amount of advance warning (e.g., 30 or 60 days) required before terminating or modifying an agreement.",
    whyItMatters: "Missing a notice deadline can automatically renew an agreement or trigger unexpected penalties.",
    category: "Obligation",
  },
]

const CATEGORIES = ["All", "Risk", "Obligation", "Financial", "Standard"] as const

export function LegalGlossary() {
  const [query, setQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string>("All")

  const filtered = LEGAL_GLOSSARY.filter((item) => {
    const matchesQuery =
      item.term.toLowerCase().includes(query.toLowerCase()) ||
      item.plainEnglish.toLowerCase().includes(query.toLowerCase()) ||
      item.whyItMatters.toLowerCase().includes(query.toLowerCase())
    const matchesCat = selectedCategory === "All" || item.category === selectedCategory
    return matchesQuery && matchesCat
  })

  const getCategoryBadge = (cat: GlossaryTerm["category"]) => {
    switch (cat) {
      case "Risk":
        return <Badge variant="destructive" className="text-xs">High Risk</Badge>
      case "Financial":
        return <Badge variant="default" className="text-xs bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-500/30">Financial</Badge>
      case "Obligation":
        return <Badge variant="secondary" className="text-xs">Obligation</Badge>
      default:
        return <Badge variant="outline" className="text-xs">Standard</Badge>
    }
  }

  return (
    <Card className="glass-panel border-border/80">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2 text-lg font-heading">
            <BookOpen className="h-5 w-5 text-primary" aria-hidden="true" />
            Plain-English Legal Glossary
          </CardTitle>
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <Input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search legal terms..."
              aria-label="Search legal terms in glossary"
              className="pl-9 h-9 text-xs"
            />
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2">
          {CATEGORIES.map((cat) => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(cat)}
              className="h-7 text-xs px-2.5 rounded-lg"
            >
              {cat}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {filtered.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">No matching legal terms found.</p>
        ) : (
          filtered.map((item) => (
            <div
              key={item.term}
              className="p-3.5 rounded-xl border border-border/60 bg-card/60 hover:border-primary/40 transition-colors space-y-1.5"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-bold text-sm text-foreground">{item.term}</span>
                {getCategoryBadge(item.category)}
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                <strong className="text-foreground">In Plain English:</strong> {item.plainEnglish}
              </p>
              <p className="text-xs text-primary/90 font-medium leading-relaxed">
                <strong className="text-foreground">Why It Matters:</strong> {item.whyItMatters}
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
