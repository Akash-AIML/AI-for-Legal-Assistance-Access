import { render, screen } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { MemoryRouter } from "react-router-dom"
import { UploadView } from "../UploadView"

describe("UploadView Component", () => {
  it("renders upload dropzone and choose files button", () => {
    const onUploadComplete = vi.fn()
    render(
      <MemoryRouter>
        <UploadView onUploadComplete={onUploadComplete} />
      </MemoryRouter>
    )
    expect(screen.getByText(/upload documents to/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /choose files to upload/i })).toBeInTheDocument()
  })

  it("renders supported file formats description and feature cards", () => {
    const onUploadComplete = vi.fn()
    render(
      <MemoryRouter>
        <UploadView onUploadComplete={onUploadComplete} />
      </MemoryRouter>
    )
    expect(screen.getByText(/PDF, DOCX, TXT, or Markdown/i)).toBeInTheDocument()
    expect(screen.getByText("Contract Compare")).toBeInTheDocument()
    expect(screen.getByText("Lawyer Brief")).toBeInTheDocument()
  })
})
