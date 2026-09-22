export interface GlossaryTerm {
  term: string
  plainEnglish: string
  whyItMatters: string
  category: "Risk" | "Obligation" | "Standard" | "Financial"
}

export const CATEGORIES = ["All", "Risk", "Obligation", "Financial", "Standard"] as const

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
