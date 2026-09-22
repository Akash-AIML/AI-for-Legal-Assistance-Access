import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { DocumentXRay } from "../DocumentXRay"
import type { DocumentInfo } from "@/lib/api"

const mockDocuments: DocumentInfo[] = [
  {
    document_id: "doc_alpha",
    title: "Lease Agreement",
    document_type: "CONTRACT",
    jurisdiction: "IN",
    version: "1",
    status: "ACTIVE",
    chunks: 12,
    governing_law: "Transfer of Property Act",
  },
  {
    document_id: "doc_beta",
    title: "Employment Agreement",
    document_type: "CONTRACT",
    jurisdiction: "IN",
    version: "1",
    status: "ACTIVE",
    chunks: 8,
    governing_law: "Indian Contract Act",
  },
]

describe("DocumentXRay Component", () => {
  it("renders document selector and analyze controls", () => {
    render(<DocumentXRay documents={mockDocuments} />)
    expect(screen.getByText("Document X-Ray")).toBeInTheDocument()
    expect(screen.getByLabelText(/select document to analyze/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/select analysis language/i)).toBeInTheDocument()
  })

  it("disables analyze button when no document is selected", () => {
    render(<DocumentXRay documents={mockDocuments} />)
    const analyzeBtn = screen.getByRole("button", { name: /run document x-ray analysis/i })
    expect(analyzeBtn).toBeDisabled()
  })

  it("includes an accessible screen reader live announcer region", () => {
    render(<DocumentXRay documents={mockDocuments} />)
    const announcer = screen.getByRole("status")
    expect(announcer).toHaveAttribute("aria-live", "assertive")
  })
})
