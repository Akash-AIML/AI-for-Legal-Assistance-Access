import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { LegalChat } from "../LegalChat"

describe("LegalChat Component", () => {
  it("renders chat input and suggestions", () => {
    render(<LegalChat />)
    expect(screen.getByPlaceholderText(/ask a question about your uploaded documents/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /send message/i })).toBeInTheDocument()
    expect(screen.getByText(/Ask Anything About Your/i)).toBeInTheDocument()
  })

  it("renders new chat and history buttons", () => {
    render(<LegalChat />)
    expect(screen.getByRole("button", { name: /new chat/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /history/i })).toBeInTheDocument()
  })

  it("contains an accessible live log region for message feed", () => {
    render(<LegalChat />)
    const logRegion = screen.getByRole("log")
    expect(logRegion).toHaveAttribute("aria-live", "polite")
    expect(logRegion).toHaveAttribute("aria-label", "Chat conversation")
  })

  it("disables send button when input is empty and enables when text is entered", () => {
    render(<LegalChat />)
    const sendBtn = screen.getByRole("button", { name: /send message/i })
    expect(sendBtn).toBeDisabled()

    const textarea = screen.getByPlaceholderText(/ask a question about your uploaded documents/i) as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: "What is the liability cap?" } })
    expect(textarea.value).toBe("What is the liability cap?")
    expect(sendBtn).toBeEnabled()
  })

  it("renders suggestion buttons with accessible labels", () => {
    render(<LegalChat />)
    const suggestionBtn = screen.getByRole("button", {
      name: /ask suggestion: what are the termination notice requirements/i,
    })
    expect(suggestionBtn).toBeInTheDocument()
  })
})
