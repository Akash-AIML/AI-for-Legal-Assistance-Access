const API_BASE = "/api"

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("legallens_token")
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  auth: {
    login: (username: string, password: string) =>
      request<{ access_token: string; user: User }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      }),
    me: () => request<User>("/auth/me"),
  },

  documents: {
    list: () => request<{ documents: DocumentInfo[]; chunk_count: number }>("/documents"),
    upload: (file: File) => {
      const formData = new FormData()
      formData.append("file", file)
      const token = localStorage.getItem("legallens_token")
      return fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      }).then((res) => {
        if (!res.ok) throw new Error("Upload failed")
        return res.json()
      })
    },
  },

  legal: {
    xray: (documentId: string) =>
      request<XRayResult>("/legal/xray", {
        method: "POST",
        body: JSON.stringify({ document_id: documentId }),
      }),
    compare: (docA: string, docB: string) =>
      request<CompareResult>("/legal/compare", {
        method: "POST",
        body: JSON.stringify({ document_a: docA, document_b: docB }),
      }),
    brief: (documentId: string) =>
      request<LawyerBriefResult>("/legal/lawyer-brief", {
        method: "POST",
        body: JSON.stringify({ document_id: documentId }),
      }),
    obligations: (documentId: string) =>
      request<ObligationsResult>("/legal/obligations", {
        method: "POST",
        body: JSON.stringify({ document_id: documentId }),
      }),
    chat: (question: string, sessionId?: string) =>
      request<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify({ question, session_id: sessionId }),
      }),
    chatStream: async (
      question: string,
      sessionId: string | undefined,
      onMeta: (meta: any) => void,
      onToken: (token: string) => void
    ) => {
      const token = localStorage.getItem("legallens_token")
      const resp = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question, session_id: sessionId }),
      })

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`)
      }

      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) return

      let buffer = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          const trimmed = line.replace(/^data:\s*/, "").trim()
          if (trimmed === "[DONE]") return
          if (!trimmed) continue
          try {
            const parsed = JSON.parse(trimmed)
            if (parsed.type === "meta") {
              onMeta(parsed)
            } else if (parsed.type === "token" && parsed.content) {
              onToken(parsed.content)
            }
          } catch {
            /* ignore */
          }
        }
      }
    },
  },
}

export function setToken(token: string) {
  localStorage.setItem("legallens_token", token)
}

export function clearToken() {
  localStorage.removeItem("legallens_token")
}

// Types
export interface User {
  username: string
  name: string
  role: string
  department: string
  jurisdiction: string
}

export interface DocumentInfo {
  document_id: string
  title: string
  document_type: string
  jurisdiction: string
  version: string
  status: string
  chunks: number
  governing_law: string
  source_path?: string
  authority_type?: string
}

export interface Finding {
  clause_type: string
  severity: "HIGH" | "MEDIUM" | "LOW"
  title: string
  explanation: string
  section: string
  source_text: string
  why_it_matters: string
  lawyer_question: string
}

export interface Obligation {
  subject: string
  action: string
  deadline: string
  condition: string
  source_section: string
  consequence?: string
}

export interface XRayResult {
  document_id: string
  title: string
  overall_risk: "HIGH" | "MEDIUM" | "LOW"
  summary: string
  findings: Finding[]
  obligations: Obligation[]
  lawyer_questions: string[]
}

export interface ClauseComparison {
  clause_type: string
  status: "SAME" | "CHANGED" | "ADDED" | "REMOVED"
  document_a_text: string
  document_b_text: string
  impact?: string
}

export interface CompareResult {
  document_a: string
  document_b: string
  summary: string
  comparisons: ClauseComparison[]
}

export interface LawyerBriefResult {
  document_id: string
  situation: string
  key_clauses: Array<{
    clause_type: string
    section: string
    why_it_matters: string
  }>
  risk_areas: Array<{
    severity: "HIGH" | "MEDIUM" | "LOW"
    description: string
    source: string
  }>
  recommended_questions: string[]
  information_to_gather: string[]
}

export interface ObligationsResult {
  document_id: string
  obligations: Obligation[]
}

export interface ChatResponse {
  answer: string
  clarification?: string
  status: string
  decision: "ANSWER" | "CLARIFY" | "RETRIEVE_MORE" | "ESCALATE"
  citations: Citation[]
  warnings: string[]
  escalation_id?: string
  session_id: string
}

export interface Citation {
  doc_id: string
  title: string
  section: string
  jurisdiction: string
  version: string
  snippet: string
}