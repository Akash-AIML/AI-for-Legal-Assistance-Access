import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { LegalGlossary } from "../LegalGlossary"

describe("LegalGlossary Component", () => {
  it("renders the glossary header and initial legal terms", () => {
    render(<LegalGlossary />)
    expect(screen.getByText("Plain-English Legal Glossary")).toBeInTheDocument()
    expect(screen.getByText("Indemnification")).toBeInTheDocument()
    expect(screen.getByText("Severability")).toBeInTheDocument()
    expect(screen.getByText("Liquidated Damages")).toBeInTheDocument()
  })

  it("filters terms when typing in the search input", () => {
    render(<LegalGlossary />)
    const searchInput = screen.getByPlaceholderText(/search legal terms/i)
    fireEvent.change(searchInput, { target: { value: "Indemnification" } })

    expect(screen.getByText("Indemnification")).toBeInTheDocument()
    expect(screen.queryByText("Force Majeure")).not.toBeInTheDocument()
  })

  it("filters terms by category when clicking a category filter button", () => {
    render(<LegalGlossary />)
    const riskButton = screen.getByRole("button", { name: /risk/i })
    fireEvent.click(riskButton)

    // Indemnification is in 'Risk' category
    expect(screen.getByText("Indemnification")).toBeInTheDocument()
    // Governing Law is in 'Standard' category, should be filtered out
    expect(screen.queryByText("Governing Law")).not.toBeInTheDocument()
  })

  it("displays no terms found message when query matches nothing", () => {
    render(<LegalGlossary />)
    const searchInput = screen.getByPlaceholderText(/search legal terms/i)
    fireEvent.change(searchInput, { target: { value: "nonexistentclause123xyz" } })

    expect(screen.getByText(/no matching legal terms found/i)).toBeInTheDocument()
  })
})
