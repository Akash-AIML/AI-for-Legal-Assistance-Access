# LegalLens — Technical Implementation Plan

## What This Is

LegalLens is an AI legal document intelligence platform built on top of an existing enterprise evidence engine. It uploads a legal document, analyzes it, and produces structured, actionable output: risk findings, clause classifications, obligation extraction, and lawyer preparation briefs.

**Not a rewrite.** ~70% of the backend stays. ~30% is new legal-specific logic. The frontend gets a new document-analysis flow but keeps the existing chat and admin infrastructure.

---

## Architecture: Actual Data Flow

### Flow 1: Document Analysis (X-Ray)

```
User uploads PDF/DOCX/TXT
    │
    ▼
POST /api/legal/analyze
    │
    ├─── 1. Parse document (existing parser.py)
    ├─── 2. Extract governing law clause (NEW: LLM call, structured output)
    ├─── 3. Build DocMetadata with legal fields (extended models.py)
    ├─── 4. Chunk + index into ChromaDB (existing chunker.py + store.py)
    ├─── 5. Retrieve all chunks for this document (existing hybrid_search, scoped to doc_id)
    ├─── 6. LLM call: classify clauses + assess risks + extract obligations (NEW: legal_engine.py)
    │       └── Uses structured output (JSON schema) for all three in one call
    └─── 7. Return DocumentXRayResult (NEW: Pydantic model)
            ├── summary: str
            ├── overall_risk: HIGH | MEDIUM | LOW
            ├── findings: list[Finding]  # each with severity, clause_type, section, explanation, source
            ├── obligations: list[Obligation]  # who, action, deadline, condition, consequence
            └── lawyer_questions: list[str]
```

### Flow 2: Document Comparison

```
User selects two indexed documents (or uploads two)
    │
    ▼
POST /api/legal/compare
    │
    ├─── 1. Retrieve all chunks from Document A
    ├─── 2. Retrieve all chunks from Document B
    ├─── 3. LLM call: align clauses semantically, compute deltas (NEW: legal_engine.py)
    │       └── Structured output: list[ClauseComparison]
    └─── 4. Return CompareResult
            ├── document_a: str
            ├── document_b: str
            ├── comparisons: list[ClauseComparison]
            │       ├── clause_type: str
            │       ├── document_a_text: str
            │       ├── document_b_text: str
            │       ├── status: SAME | CHANGED | ADDED | REMOVED
            │       └── impact: str  # plain-English explanation of why it matters
            └── summary: str
```

### Flow 3: Legal Q&A (Existing, Rebranded)

```
User asks a question about a document
    │
    ▼
POST /api/chat (existing endpoint, no changes needed)
    │
    └─── Existing LangGraph pipeline: understand → retrieve → assess → decide → answer
         The only change: system prompt says "legal assistant" instead of "enterprise compliance assistant"
```

### Flow 4: Lawyer Brief (Derived from X-Ray)

```
GET /api/legal/lawyer-brief?document_id=X
    │
    ├─── 1. Load existing X-Ray result for document (or run X-Ray if not cached)
    ├─── 2. LLM call: transform X-Ray findings into lawyer-ready format (NEW: legal_engine.py)
    └─── 3. Return LawyerBrief
            ├── situation: str
            ├── key_clauses: list[dict]  # section, clause_type, why_it_matters
            ├── risk_areas: list[dict]   # severity, description, source
            ├── recommended_questions: list[str]
            └── information_to_gather: list[str]  # "Bring your original offer letter", etc.
```

---

## Files to Modify

### Backend

| File | Action | What Changes |
|------|--------|-------------|
| `backend/src/models.py` | MODIFY | Add `AuthorityType`, `ClauseType`, `RiskLevel`, `Finding`, `Obligation`, `ClauseComparison`, `DocumentXRayResult`, `LawyerBrief` models. Extend `DocMetadata` with `authority_type`, `governing_law`, `country`, `state`, `expiry_date`, `citation`. |
| `backend/src/ingestion/safety.py` | NEW | One function: `wrap_untrusted(content: str) -> str` that wraps document text in delimiters. One constant: `UNTRUSTED_MARKER`. |
| `backend/src/ingestion/ingestor.py` | MODIFY | After parsing, call LLM to extract governing law and populate new metadata fields. |
| `backend/src/legal_engine.py` | NEW | Core module. Contains: `analyze_document(chunks) -> DocumentXRayResult`, `compare_documents(chunks_a, chunks_b) -> CompareResult`, `generate_lawyer_brief(xray) -> LawyerBrief`. All use structured output. |
| `backend/src/api/legal_routes.py` | NEW | Four endpoints: `POST /api/legal/analyze`, `POST /api/legal/compare`, `GET /api/legal/lawyer-brief`, `GET /api/legal/obligations`. |
| `backend/src/graph/nodes.py` | MODIFY | Change `SYSTEM_GROUNDED` prompt from "enterprise compliance assistant" to "legal document assistant". |
| `backend/src/main.py` | MODIFY | Register `legal_routes.router`. Change FastAPI title/description. |
| `backend/src/config.py` | MODIFY | Change `collection_name` default to `legal_docs`. |
| `scripts/seed_corpus.py` | REWRITE | Replace enterprise policies with sample legal documents (see below). |

### Frontend

| File | Action | What Changes |
|------|--------|-------------|
| `frontend/src/App.jsx` | MODIFY | Add view routing for `xray`, `compare`. Add nav tabs. |
| `frontend/src/api.js` | MODIFY | Add `legalXray(docId)`, `legalCompare(docA, docB)`, `legalBrief(docId)`, `legalObligations(docId)`. |
| `frontend/src/components/DocumentXRay.jsx` | NEW | Main analysis view: risk summary, findings cards, obligations list, lawyer questions. |
| `frontend/src/components/ContractCompareView.jsx` | NEW | Side-by-side clause comparison with delta indicators. |
| `frontend/src/components/Chat.jsx` | MODIFY | Rebrand text only. Change "enterprise policies" to "legal documents". Change suggestions to legal queries. |
| `frontend/src/components/Admin.jsx` | MODIFY | Rebrand text only. |

### Tests

| File | Action | What Changes |
|------|--------|-------------|
| `tests/test_decision.py` | VERIFY | Must pass unchanged. |
| `tests/test_legal_engine.py` | NEW | Test that `analyze_document` returns valid `DocumentXRayResult`. Test that `compare_documents` returns valid `CompareResult`. Test prompt injection defense. |

---

## Seed Corpus: Sample Legal Documents

Replace the enterprise policy corpus with these:

1. **Employment Agreement (India)** — ACTIVE, has IP assignment clause, 90-day termination notice, mandatory arbitration, non-compete. This is the primary demo document.
2. **Employment Agreement (India, v2)** — SUPERSEDED version with different terms (30-day notice, no non-compete). Used for contract comparison demo.
3. **Non-Disclosure Agreement (NDA)** — ACTIVE, bilateral NDA with confidentiality obligations and term.
4. **Service Agreement (SaaS)** — ACTIVE, B2B service agreement with liability cap, SLA, data processing addendum.
5. **Rental Agreement (India)** — ACTIVE, residential lease with deposit, notice period, maintenance obligations.
6. **GDPR Data Processing Agreement** — ACTIVE, EU jurisdiction, data processor obligations.

Each document uses the extended metadata schema with `authority_type: CONTRACT`, `governing_law`, `jurisdiction`, etc.

---

## Legal Engine: Structured Output Schemas

### Document X-Ray Schema

```python
class Finding(BaseModel):
    clause_type: ClauseType  # enum: TERMINATION, IP_ASSIGNMENT, INDEMNITY, etc.
    severity: RiskLevel      # HIGH, MEDIUM, LOW
    section: str             # "§14.1" or "Section 3.2"
    title: str               # "Broad IP Assignment"
    explanation: str         # plain-English, 2-3 sentences
    source_text: str         # original clause text
    why_it_matters: str      # practical implication
    lawyer_question: str     # specific question to ask a lawyer

class Obligation(BaseModel):
    subject: str             # "Employee" or "Employer"
    action: str              # "Provide written notice"
    deadline: str            # "90 days before termination"
    condition: str           # "If employee wants to terminate"
    source_section: str      # "§14.1"
    consequence: str         # "Contractual requirements apply"

class DocumentXRayResult(BaseModel):
    document_id: str
    title: str
    overall_risk: RiskLevel
    summary: str             # 3-5 sentence plain-English summary
    findings: list[Finding]
    obligations: list[Obligation]
    lawyer_questions: list[str]
```

### Comparison Schema

```python
class ClauseComparison(BaseModel):
    clause_type: ClauseType
    document_a_text: str
    document_b_text: str
    status: str  # "SAME", "CHANGED", "ADDED", "REMOVED"
    impact: str  # plain-English: "Notice period increased from 30 to 90 days, giving less flexibility to terminate"

class CompareResult(BaseModel):
    document_a_id: str
    document_b_id: str
    comparisons: list[ClauseComparison]
    summary: str
```

### Lawyer Brief Schema

```python
class LawyerBrief(BaseModel):
    document_id: str
    situation: str           # "Employment contract received on 15 Sep 2026 for a software engineer role in India"
    key_clauses: list[dict]  # [{section, clause_type, why_it_matters}]
    risk_areas: list[dict]   # [{severity, description, source}]
    recommended_questions: list[str]
    information_to_gather: list[str]
```

---

## Implementation Phases

### Phase 0: Foundation (Day 1, Parallel)
- [ ] Rewrite seed corpus with 6 sample legal documents
- [ ] Extend `models.py` with new types and Pydantic models
- [ ] Add `safety.py` (wrap_untrusted function)
- [ ] Rebrand: README, FastAPI title, UI text, sidebar labels

### Phase 1: Backend Core (Day 1-2, Sequential)
- [ ] Create `legal_engine.py` with `analyze_document()`, `compare_documents()`, `generate_lawyer_brief()`
- [ ] Create `legal_routes.py` with 4 endpoints
- [ ] Modify `ingestor.py` to extract governing law during ingestion
- [ ] Register routes in `main.py`
- [ ] Change system prompt in `nodes.py`

### Phase 2: Frontend (Day 2-3, Parallel)
- [ ] Create `DocumentXRay.jsx` component
- [ ] Create `ContractCompareView.jsx` component
- [ ] Update `App.jsx` with new view routing and nav
- [ ] Update `api.js` with new endpoints
- [ ] Update `Chat.jsx` suggestions and branding

### Phase 3: Tests & Polish (Day 3, Parallel)
- [ ] Write `test_legal_engine.py` (3-5 test cases)
- [ ] Verify existing `test_decision.py` still passes
- [ ] Run full demo flow end-to-end
- [ ] Final rebrand pass (no "Nexus" or "Enterprise Compliance" anywhere)

---

## What NOT to Build

1. **Do not build a separate timeline component.** The obligations list in the X-Ray IS the timeline. Adding a separate component doubles the work for the same data.

2. **Do not build a separate clause classifier module.** Clause classification is one field in the Finding model, output by the same LLM call that produces risk analysis. One prompt, one call, one structured output.

3. **Do not add obligation tracking with deadlines relative to "today".** That requires date parsing and state management. For a hackathon, obligations are static extracted objects, not a live tracker.

4. **Do not redesign the entire frontend.** The existing chat UI is fine. Add a new document analysis view. Keep the sidebar navigation. Don't rebuild from scratch.

5. **Do not add more than 6 seed documents.** Diminishing returns. Six documents cover all the demo scenarios.

6. **Do not add RBAC to the legal endpoints.** The challenge is about accessibility, not enterprise security. Remove the admin requirement for upload and analysis. Anyone can upload and analyze.

7. **Do not add streaming to the X-Ray endpoint.** The analysis takes 3-5 seconds. Show a loading spinner. Streaming adds complexity without demo value.

---

## Verification: What "Done" Looks Like

### Automated
```bash
# Existing tests still pass
pytest tests/test_decision.py -v

# New legal engine tests pass
pytest tests/test_legal_engine.py -v
```

### Manual Demo Flow
1. Open the app → see "LegalLens" branding, document upload as hero feature
2. Upload the sample employment agreement → see Document X-Ray with risk findings
3. Click a finding → see source clause, plain-English explanation, lawyer question
4. Upload two versions of the same contract → see side-by-side comparison with deltas
5. Click "Prepare for Lawyer" → see structured lawyer brief with questions
6. Ask a question about the document → get grounded answer with citations
7. Upload a document with injection attempt → system treats it as normal text

### Judge-Facing Pitch
"We built an evidence-first legal AI that doesn't just summarize a document — it determines what the evidence supports, identifies what deserves attention, explains it in plain language, and knows when it should ask for more information or hand the issue to a professional."
