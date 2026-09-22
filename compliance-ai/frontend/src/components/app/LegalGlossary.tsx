"use client"

import { useState } from "react"
import { BookOpen, Search } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CATEGORIES, LEGAL_GLOSSARY, type GlossaryTerm } from "./legalGlossaryData"

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
              aria-pressed={selectedCategory === cat}
              aria-label={`Filter by ${cat}`}
              className="h-7 text-xs px-2.5 rounded-lg"
            >
              {cat}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No matching legal terms found. Try a different keyword or filter.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filtered.map((item) => (
              <div
                key={item.term}
                className="p-3.5 rounded-xl border border-border/70 bg-card/50 hover:bg-card/80 transition-colors flex flex-col justify-between gap-2 shadow-xs"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <h3 className="font-semibold text-sm text-foreground">{item.term}</h3>
                    {getCategoryBadge(item.category)}
                  </div>
                  <p className="text-xs text-foreground/90 leading-relaxed font-sans">
                    {item.plainEnglish}
                  </p>
                </div>
                <div className="text-[11px] text-muted-foreground bg-muted/40 p-2 rounded-lg border border-border/40">
                  <span className="font-semibold text-primary/90">Why it matters: </span>
                  {item.whyItMatters}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
