import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { ContractCompare } from "../ContractCompare"
import type { DocumentInfo } from "@/lib/api"
import { api } from "@/lib/api"

vi.mock("@/lib/api", () => ({
  api: {
    legal: {
      compare: vi.fn(),
    },
  },
}))

const mockDocuments: DocumentInfo[] = [
  {
    document_id: "doc_1",
    title: "Standard NDA",
    document_type: "CONTRACT",
    jurisdiction: "IN",
    version: "1",
    status: "ACTIVE",
    chunks: 5,
    governing_law: "Indian Contract Act",
  },
  {
    document_id: "doc_2",
    title: "Revised NDA",
    document_type: "CONTRACT",
    jurisdiction: "IN",
    version: "2",
    status: "ACTIVE",
    chunks: 6,
    governing_law: "Indian Contract Act",
  },
]

describe("ContractCompare Component", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renders comparison selectors and disabled compare button initially", () => {
    render(<ContractCompare documents={mockDocuments} />)
    expect(screen.getByText("Contract Compare")).toBeInTheDocument()
    expect(screen.getByLabelText(/select first document to compare/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/select second document to compare/i)).toBeInTheDocument()

    const compareBtn = screen.getByRole("button", { name: /compare selected documents/i })
    expect(compareBtn).toBeDisabled()
  })

  it("includes an accessible screen reader live status region", () => {
    render(<ContractCompare documents={mockDocuments} />)
    const statusRegion = screen.getByRole("status")
    expect(statusRegion).toHaveAttribute("aria-live", "polite")
  })

  it("renders comparison results and clause tooltips upon successful comparison", async () => {
    vi.mocked(api.legal.compare).mockResolvedValueOnce({
      document_a: "doc_1",
      document_b: "doc_2",
      comparisons: [
        {
          clause_type: "TERMINATION",
          document_a_text: "30 days notice",
          document_b_text: "60 days notice",
          status: "CHANGED",
          impact: "Notice period increased.",
        },
      ],
      summary: "Comparison summary: notice duration was increased.",
    })

    render(<ContractCompare documents={mockDocuments} />)

    // Select Doc A
    const triggerA = screen.getByLabelText(/select first document to compare/i)
    fireEvent.click(triggerA)
    const optionA = await screen.findByRole("option", { name: /standard nda/i })
    fireEvent.click(optionA)

    // Select Doc B
    const triggerB = screen.getByLabelText(/select second document to compare/i)
    fireEvent.click(triggerB)
    const optionB = await screen.findByRole("option", { name: /revised nda/i })
    fireEvent.click(optionB)

    const compareBtn = screen.getByRole("button", { name: /compare selected documents/i })
    expect(compareBtn).toBeEnabled()
    fireEvent.click(compareBtn)

    await waitFor(() => {
      expect(screen.getByText("Clause-by-Clause Comparison")).toBeInTheDocument()
      expect(screen.getByText("Notice period increased.")).toBeInTheDocument()
      expect(screen.getByRole("button", { name: /glossary definition for termination/i })).toBeInTheDocument()
    })
  })
})
