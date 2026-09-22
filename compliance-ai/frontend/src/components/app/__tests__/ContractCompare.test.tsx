import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { ContractCompare } from "../ContractCompare"
import type { DocumentInfo } from "@/lib/api"

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
  it("renders comparison selectors and disabled compare button initially", () => {
    render(<ContractCompare documents={mockDocuments} />)
    expect(screen.getByText("Contract Compare")).toBeInTheDocument()
    expect(screen.getByLabelText(/select first document to compare/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/select second document to compare/i)).toBeInTheDocument()

    const compareBtn = screen.getByRole("button", { name: /compare selected documents/i })
    expect(compareBtn).toBeDisabled()
  })
})
