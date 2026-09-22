import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { LawyerBrief } from "../LawyerBrief"
import type { DocumentInfo, LawyerBriefResult } from "@/lib/api"
import { api } from "@/lib/api"

vi.mock("@/lib/api", () => ({
  api: {
    legal: {
      brief: vi.fn(),
    },
  },
}))

const mockDocuments: DocumentInfo[] = [
  {
    document_id: "doc_nda",
    title: "Mutual NDA",
    document_type: "CONTRACT",
    jurisdiction: "IN",
    version: "1",
    status: "ACTIVE",
    chunks: 10,
    governing_law: "Indian Contract Act",
  },
]

const mockBriefResult: LawyerBriefResult = {
  document_id: "doc_nda",
  situation: "This mutual NDA covers confidentiality for tech evaluation.",
  key_clauses: [
    {
      clause_type: "CONFIDENTIALITY",
      section: "Section 2.1",
      why_it_matters: "Defines proprietary information and obligations.",
    },
  ],
  risk_areas: [
    {
      severity: "HIGH",
      description: "Indefinite duration of trade secret obligations.",
      source: "Section 5",
    },
  ],
  recommended_questions: ["Is the non-solicit clause enforceable in India?"],
  information_to_gather: ["Copy of mutual disclosure schedules"],
}

describe("LawyerBrief Component", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renders header, language selector, and document selector", () => {
    render(<LawyerBrief documents={mockDocuments} />)
    expect(screen.getByRole("heading", { name: "Lawyer Brief", level: 1 })).toBeInTheDocument()
    expect(screen.getByLabelText(/select document to generate lawyer brief/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/select brief language/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /generate lawyer brief/i })).toBeInTheDocument()
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite")
  })

  it("disables generate button when no document is selected", () => {
    render(<LawyerBrief documents={mockDocuments} />)
    const generateBtn = screen.getByRole("button", { name: /generate lawyer brief/i })
    expect(generateBtn).toBeDisabled()
  })

  it("renders brief results and print button upon successful generation", async () => {
    vi.mocked(api.legal.brief).mockResolvedValueOnce(mockBriefResult)

    render(<LawyerBrief documents={mockDocuments} />)

    // Select document via select trigger
    const trigger = screen.getByLabelText(/select document to generate lawyer brief/i)
    fireEvent.click(trigger)

    // In Radix Select, select the item
    const option = await screen.findByRole("option", { name: /mutual nda/i })
    fireEvent.click(option)

    const generateBtn = screen.getByRole("button", { name: /generate lawyer brief/i })
    expect(generateBtn).toBeEnabled()
    fireEvent.click(generateBtn)

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /generated lawyer brief/i })).toBeInTheDocument()
      expect(screen.getByText("Situation Summary")).toBeInTheDocument()
      expect(screen.getByText("This mutual NDA covers confidentiality for tech evaluation.")).toBeInTheDocument()
      expect(screen.getByRole("button", { name: /print or save lawyer brief as pdf/i })).toBeInTheDocument()
    })
  })

  it("renders error alert when brief generation fails", async () => {
    vi.mocked(api.legal.brief).mockRejectedValueOnce(new Error("Network connection dropped"))

    render(<LawyerBrief documents={mockDocuments} />)

    const trigger = screen.getByLabelText(/select document to generate lawyer brief/i)
    fireEvent.click(trigger)
    const option = await screen.findByRole("option", { name: /mutual nda/i })
    fireEvent.click(option)

    const generateBtn = screen.getByRole("button", { name: /generate lawyer brief/i })
    fireEvent.click(generateBtn)

    await waitFor(() => {
      expect(screen.getByText("Network connection dropped")).toBeInTheDocument()
    })
  })
})
