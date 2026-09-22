import "@testing-library/jest-dom"

// Mock window.matchMedia for components that use media queries
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
})

// Mock window.scrollTo
window.scrollTo = () => {}

// Prevent happy-dom animation cancelation from bubbling as unhandled rejection
const isAnimationAbort = (err: any) =>
  err?.name === "AbortError" ||
  (typeof err?.message === "string" && err.message.includes("animation was canceled"))

window.addEventListener("unhandledrejection", (event) => {
  if (isAnimationAbort(event.reason)) {
    event.preventDefault()
  }
})

;(globalThis as { process?: { on?: (event: string, cb: (reason: unknown) => void) => void } }).process?.on?.(
  "unhandledRejection",
  (reason: unknown) => {
    if (isAnimationAbort(reason)) {
      return
    }
  }
)
