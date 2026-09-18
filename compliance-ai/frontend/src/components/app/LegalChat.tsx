"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Shield,
  Send,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  AlertCircle,
  Clock,
  Lock,
  Sparkles,
  Plus,
  History,
  Trash2,
  MessageSquare
} from "lucide-react"
import { api, type Citation } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { cn } from "@/lib/utils"

const STATUS_CONFIG: Record<string, { label: string; icon: React.ReactNode }> = {
  SUPPORTED: { label: "Grounded Answer", icon: <CheckCircle2 className="h-3 w-3" /> },
  AMBIGUOUS: { label: "Clarification Required", icon: <HelpCircle className="h-3 w-3" /> },
  INSUFFICIENT_EVIDENCE: { label: "Insufficient Data", icon: <AlertCircle className="h-3 w-3" /> },
  CONFLICTING_EVIDENCE: { label: "Conflict Detected", icon: <AlertTriangle className="h-3 w-3" /> },
  OUTDATED_EVIDENCE: { label: "Outdated Source", icon: <Clock className="h-3 w-3" /> },
  RESTRICTED: { label: "Restricted Access", icon: <Lock className="h-3 w-3" /> },
}

interface Message {
  role: "user" | "assistant"
  content: string
  meta?: {
    status?: string
    decision?: string
    citations?: Citation[]
    warnings?: string[]
    escalation?: string
  }
}

interface ChatSession {
  id: string
  title: string
  createdAt: string
  messages: Message[]
}

const STORAGE_KEY = "legallens_chat_history"

const SUGGESTIONS = [
  "What are the termination notice requirements in this agreement?",
  "Is there an IP assignment or work product clause?",
  "What are the confidentiality obligations and exclusions?",
  "What is the liability cap specified in the agreement?",
  "Which governing law and jurisdiction applies?",
]

export function LegalChat() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [busy, setBusy] = useState(false)
  const [showHistory, setShowHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load chat sessions history from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed: ChatSession[] = JSON.parse(stored)
        setSessions(parsed)
        if (parsed.length > 0) {
          setActiveSessionId(parsed[0].id)
          setMessages(parsed[0].messages || [])
        }
      }
    } catch {
      /* ignore */
    }
  }, [])

  // Sync sessions state to localStorage
  const saveSessions = useCallback((updatedSessions: ChatSession[]) => {
    setSessions(updatedSessions)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedSessions))
    } catch {
      /* ignore */
    }
  }, [])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, busy, scrollToBottom])

  // Select a session from history
  const selectSession = (session: ChatSession) => {
    setActiveSessionId(session.id)
    setMessages(session.messages || [])
  }

  // Start a new blank chat session
  const startNewChat = () => {
    setActiveSessionId(null)
    setMessages([])
    setInput("")
  }

  // Delete a single chat session
  const deleteSession = (e: React.MouseEvent, idToDelete: string) => {
    e.stopPropagation()
    const updated = sessions.filter((s) => s.id !== idToDelete)
    saveSessions(updated)
    if (activeSessionId === idToDelete) {
      if (updated.length > 0) {
        setActiveSessionId(updated[0].id)
        setMessages(updated[0].messages || [])
      } else {
        startNewChat()
      }
    }
  }

  // Clear all history
  const clearAllHistory = () => {
    saveSessions([])
    startNewChat()
  }

  // Send message
  const send = useCallback(
    async (text?: string) => {
      const q = (text ?? input).trim()
      if (!q || busy) return
      setInput("")

      const userMsg: Message = { role: "user", content: q }
      const newMessages = [...messages, userMsg]
      setMessages(newMessages)
      setBusy(true)

      let currentId = activeSessionId
      let currentSessions = [...sessions]

      if (!currentId) {
        // Create new session
        currentId = `session_${Date.now()}`
        setActiveSessionId(currentId)
        const newSession: ChatSession = {
          id: currentId,
          title: q.length > 36 ? q.slice(0, 36) + "..." : q,
          createdAt: new Date().toISOString(),
          messages: newMessages,
        }
        currentSessions = [newSession, ...currentSessions]
      } else {
        // Update existing session
        currentSessions = currentSessions.map((s) =>
          s.id === currentId ? { ...s, messages: newMessages } : s
        )
      }
      saveSessions(currentSessions)

      try {
        console.time("⏱️ [FE-PERF] Streaming Chat Request Total")
        console.log("%c⏱️ [FE-PERF] Dispatching question to SSE stream:", "color: #38bdf8; font-weight: bold;", q)
        const t0 = performance.now()

        let metaData: any = null
        let accumulatedText = ""
        let firstTokenLogged = false

        // Add placeholder assistant message for live streaming
        setMessages((prev) => [...prev, { role: "assistant", content: "", meta: {} }])

        await api.legal.chatStream(
          q,
          currentId || undefined,
          (meta) => {
            metaData = meta
            const dtMeta = performance.now() - t0
            console.log(`%c⏱️ [FE-PERF] Received metadata & ${meta.citations?.length || 0} citations in ${dtMeta.toFixed(1)}ms`, "color: #a855f7; font-weight: bold;")
            setMessages((prev) => {
              const copy = [...prev]
              const last = copy[copy.length - 1]
              if (last && last.role === "assistant") {
                copy[copy.length - 1] = {
                  ...last,
                  meta: {
                    status: meta.status,
                    decision: meta.decision,
                    citations: meta.citations,
                  },
                }
              }
              return copy
            })
          },
          (token) => {
            if (!firstTokenLogged) {
              const ttft = performance.now() - t0
              console.log(`%c⏱️ [FE-PERF] First Token Rendered in ${ttft.toFixed(1)}ms (${(ttft/1000).toFixed(2)}s)!`, "color: #4ade80; font-weight: bold;")
              firstTokenLogged = true
            }
            accumulatedText += token
            setMessages((prev) => {
              const copy = [...prev]
              const last = copy[copy.length - 1]
              if (last && last.role === "assistant") {
                copy[copy.length - 1] = {
                  ...last,
                  content: accumulatedText,
                }
              }
              return copy
            })
          }
        )

        const totalDt = performance.now() - t0
        console.log(`%c⏱️ [FE-PERF] Stream Complete in ${totalDt.toFixed(1)}ms (${(totalDt / 1000).toFixed(2)}s)`, "color: #4ade80; font-weight: bold;")
        console.timeEnd("⏱️ [FE-PERF] Streaming Chat Request Total")

        const assistantMsg: Message = {
          role: "assistant",
          content: accumulatedText,
          meta: {
            status: metaData?.status || "SUPPORTED",
            decision: metaData?.decision || "ANSWER",
            citations: metaData?.citations || [],
          },
        }

        const finalMessages = [...newMessages, assistantMsg]
        const updatedSessions = currentSessions.map((s) =>
          s.id === currentId ? { ...s, messages: finalMessages } : s
        )
        saveSessions(updatedSessions)
      } catch (e: any) {
        const errorMsg: Message = {
          role: "assistant",
          content: `Error: ${e.message}`,
        }
        const finalMessages = [...newMessages, errorMsg]
        setMessages(finalMessages)

        const updatedSessions = currentSessions.map((s) =>
          s.id === currentId ? { ...s, messages: finalMessages } : s
        )
        saveSessions(updatedSessions)
      } finally {
        setBusy(false)
      }
    },
    [input, busy, messages, activeSessionId, sessions, saveSessions]
  )

  const getStatusVariant = (status?: string) => {
    switch (status) {
      case "SUPPORTED":
        return "default"
      case "RESTRICTED":
      case "CONFLICTING_EVIDENCE":
        return "destructive"
      default:
        return "secondary"
    }
  }

  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr)
      const now = new Date()
      if (d.toDateString() === now.toDateString()) {
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }
      return d.toLocaleDateString([], { month: "short", day: "numeric" })
    } catch {
      return ""
    }
  }

  return (
    <div className="flex h-[calc(100vh-6.5rem)] flex-col max-w-6xl mx-auto space-y-3">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-border/80 px-1">
        <div>
          <h1 className="font-heading text-xl sm:text-2xl font-bold text-foreground flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            <span>Legal Q&A Assistant</span>
          </h1>
          <p className="text-xs text-muted-foreground">
            Evidence-grounded answers backed by contract section citations & history
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle History Panel */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHistory(!showHistory)}
            className="h-8 text-xs font-semibold gap-1.5 border-border/80 hover:bg-accent"
          >
            <History className="h-3.5 w-3.5 text-primary" />
            <span className="hidden sm:inline">History</span>
            {sessions.length > 0 && (
              <Badge variant="secondary" className="px-1.5 py-0 text-[10px] h-4 ml-0.5">
                {sessions.length}
              </Badge>
            )}
          </Button>

          {/* New Chat Button */}
          <Button
            size="sm"
            onClick={startNewChat}
            className="h-8 text-xs font-semibold gap-1.5 shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Chat</span>
          </Button>
        </div>
      </div>

      {/* Main Content Layout (Flex Row with History Panel & Chat Window) */}
      <div className="flex-1 flex gap-3 overflow-hidden">
        {/* History Sidebar Panel */}
        <AnimatePresence initial={false}>
          {showHistory && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
              className="hidden lg:flex flex-col shrink-0 rounded-2xl glass-panel border border-border/80 overflow-hidden"
            >
              <div className="flex items-center justify-between p-3 border-b border-border/80 bg-muted/30">
                <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <History className="h-3.5 w-3.5 text-primary" />
                  <span>Saved Threads</span>
                </span>
                {sessions.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearAllHistory}
                    className="h-6 px-2 text-[10px] text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                  >
                    Clear All
                  </Button>
                )}
              </div>

              <ScrollArea className="flex-1 p-2">
                {sessions.length === 0 ? (
                  <div className="flex flex-col items-center justify-center p-6 text-center text-muted-foreground">
                    <History className="h-8 w-8 mb-2 opacity-30 text-primary" />
                    <p className="text-xs font-medium">No saved chat history</p>
                    <p className="text-[10px] text-muted-foreground mt-1">
                      Your Q&A sessions will automatically save here
                    </p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {sessions.map((s) => {
                      const isActive = s.id === activeSessionId
                      return (
                        <div
                          key={s.id}
                          onClick={() => selectSession(s)}
                          className={cn(
                            "flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all text-xs group",
                            isActive
                              ? "bg-secondary text-foreground font-semibold shadow-sm border-l-2 border-primary"
                              : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                          )}
                        >
                          <div className="min-w-0 flex-1 pr-2">
                            <p className="truncate text-xs font-medium leading-tight text-foreground">
                              {s.title}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[10px] text-muted-foreground">
                                {formatDate(s.createdAt)}
                              </span>
                              <span className="text-[10px] text-muted-foreground">
                                • {s.messages?.length || 0} msgs
                              </span>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => deleteSession(e, s.id)}
                            className="h-6 w-6 opacity-0 group-hover:opacity-100 hover:text-destructive hover:bg-destructive/10 transition-opacity shrink-0"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      )
                    })}
                  </div>
                )}
              </ScrollArea>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Chat Feed & Input Area */}
        <div className="flex-1 overflow-hidden rounded-2xl glass-panel border border-border/80 flex flex-col">
          {/* Scrollable Message List */}
          <ScrollArea className="flex-1 p-4 sm:p-6">
            <div className="space-y-6">
              {/* Empty State Suggestion Prompt Cards */}
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center py-10 min-h-[350px] text-center">
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.05, type: "spring", stiffness: 200 }}
                    className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 text-primary shadow-glow"
                  >
                    <Shield className="h-7 w-7" />
                  </motion.div>
                  <h2 className="font-heading text-xl font-bold text-foreground mb-1">
                    Ask Anything About Your{" "}
                    <span className="bg-gradient-to-r from-blue-400 to-amber-300 bg-clip-text text-transparent">
                      Indexed Documents
                    </span>
                  </h2>
                  <p className="text-xs sm:text-sm text-muted-foreground max-w-md mb-6 leading-relaxed">
                    LegalLens evaluates retrieved chunks, checks jurisdiction precedence, and
                    provides answers backed by source citations.
                  </p>
                  <StaggerContainer staggerDelay={0.06} className="w-full max-w-lg space-y-2">
                    {SUGGESTIONS.map((s) => (
                      <StaggerItem key={s} direction="up">
                        <Card
                          className="p-3 text-left cursor-pointer glass-panel hover:border-primary/40 transition-all group"
                          onClick={() => send(s)}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs sm:text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                              {s}
                            </span>
                            <Sparkles className="h-3.5 w-3.5 text-primary opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2" />
                          </div>
                        </Card>
                      </StaggerItem>
                    ))}
                  </StaggerContainer>
                </div>
              )}

              {/* Render Chat Messages with strict user/assistant alignment */}
              <AnimatePresence>
                {messages.map((m, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    className={cn("flex w-full", m.role === "user" ? "justify-end" : "justify-start")}
                  >
                    {/* Message Bubble Container */}
                    <div
                      className={cn(
                        "flex flex-col space-y-2",
                        m.role === "user"
                          ? "items-end max-w-[80%] sm:max-w-[70%]"
                          : "items-start max-w-[90%] sm:max-w-[85%]"
                      )}
                    >
                      {/* Status Badges for Assistant */}
                      {m.role === "assistant" && m.meta?.status && (
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={getStatusVariant(m.meta.status)}
                            className="text-[10px] gap-1 px-2 py-0.5"
                          >
                            {STATUS_CONFIG[m.meta.status]?.icon}
                            <span>{STATUS_CONFIG[m.meta.status]?.label || m.meta.status}</span>
                          </Badge>
                          {m.meta.decision === "ESCALATE" && (
                            <Badge variant="destructive" className="text-[10px] gap-1 px-2 py-0.5">
                              <Lock className="h-3 w-3" /> Escalated to Counsel
                            </Badge>
                          )}
                        </div>
                      )}

                      {/* Chat Bubble Body */}
                      <div
                        className={cn(
                          "rounded-2xl p-4 text-sm font-sans leading-relaxed shadow-sm transition-all",
                          m.role === "user"
                            ? "bg-primary text-primary-foreground font-medium rounded-tr-sm ml-auto"
                            : "bg-card border border-border/80 text-foreground rounded-tl-sm glass-panel mr-auto"
                        )}
                      >
                        <p className="whitespace-pre-wrap">{m.content}</p>
                      </div>

                      {/* Assistant Warnings */}
                      {m.role === "assistant" && m.meta?.warnings && m.meta.warnings.length > 0 && (
                        <div className="w-full space-y-1">
                          {m.meta.warnings.map((w, warningIdx) => (
                            <div
                              key={warningIdx}
                              className="flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-400"
                            >
                              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                              <span>{w}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Assistant Source Citation Cards */}
                      {m.role === "assistant" &&
                        m.meta?.citations &&
                        m.meta.citations.length > 0 && (
                          <div className="w-full space-y-2 pt-2">
                            <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                              Source Citations ({m.meta.citations.length})
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full">
                              {m.meta.citations.map((c: Citation, citeIdx: number) => (
                                <Card
                                  key={citeIdx}
                                  className="glass-panel p-3 border-border/60 hover:border-primary/40 transition-all"
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-bold text-foreground truncate">
                                      {c.title || c.doc_id}
                                    </span>
                                    <Badge
                                      variant="outline"
                                      className="text-[9px] px-1.5 py-0 shrink-0"
                                    >
                                      {c.jurisdiction || "GLOBAL"}
                                    </Badge>
                                  </div>
                                  <p className="text-[11px] font-mono text-muted-foreground mb-1.5">
                                    Section: {c.section}
                                  </p>
                                  <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed bg-muted/40 p-2 rounded-lg border border-border/40 font-mono text-[11px]">
                                    "{c.snippet}"
                                  </p>
                                </Card>
                              ))}
                            </div>
                          </div>
                        )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Busy Spinner Bubble */}
              {busy && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/15 text-primary border border-primary/30">
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  </div>
                  <div className="rounded-2xl glass-panel px-4 py-2.5 text-xs text-muted-foreground border border-border/80">
                    Evaluating evidence and checking jurisdiction precedence...
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Bottom Sticky Input Form Bar */}
          <div className="border-t border-border/80 p-3 bg-card/80 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Ask a question about your uploaded documents..."
                className="flex-1 bg-muted/40 border border-border/60 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-primary/60 transition-colors"
              />
              <Button
                onClick={() => send()}
                disabled={busy || !input.trim()}
                size="default"
                className="gap-2 font-semibold px-4 shadow-sm"
              >
                <span>Send</span>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}