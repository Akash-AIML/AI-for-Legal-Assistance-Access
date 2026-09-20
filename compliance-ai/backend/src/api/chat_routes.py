"""Chat routes: run the LangGraph decision workflow, persist history + audit."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_current_user, get_optional_user, to_frame
from graph.builder import get_graph
from memory import store as memory
from models import Decision

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/sessions")
def sessions(user: dict = Depends(get_optional_user)):
    return {"sessions": memory.list_sessions(user["username"])}


@router.get("/history")
def history(session_id: str, user: dict = Depends(get_optional_user)):
    msgs = memory.get_history(session_id, limit=50)
    return {"session_id": session_id, "messages": msgs}


import time

@router.post("")
def chat(payload: dict, user: dict = Depends(get_optional_user)):
    t_start = time.time()
    question = (payload.get("question") or payload.get("message") or "").strip()
    if not question:
        return {"error": "empty message"}

    print(f"\n\033[94m🚀 [API-PERF] POST /api/chat started | Question: '{question[:60]}...'\033[0m", flush=True)

    session_id = payload.get("session_id")
    session = memory.get_session(session_id) if session_id else None
    if not session:
        session = memory.create_session(user["username"])
        session_id = session["session_id"]

    frame = to_frame(user, session_id)

    # merge structured conversation context accumulated across turns
    if session and session.get("context"):
        for k, v in session["context"].items():
            if getattr(frame, k, None) in ("", None) and v:
                setattr(frame, k, v)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in memory.get_history(session_id, limit=8)
    ]

    state = {
        "question": question,
        "frame": frame,
        "history": history,
        "retries": 0,
        "decision": None,
        "answer": "",
        "citations": [],
        "clarification": "",
        "escalation": None,
        "evidence": [],
        "understood": {},
        "assessment": None,
        "restricted": False,
        "trace": [],
    }

    out = get_graph().invoke(state)
    assessment = out["assessment"]
    status = assessment.status.value if assessment else "NONE"
    decision = out["decision"].value if out["decision"] else "NONE"

    memory.add_message(session_id, "user", question)
    memory.add_message(
        session_id,
        "assistant",
        out.get("answer") or out.get("clarification") or "",
        meta={"status": status, "decision": decision, "citations": out.get("citations", [])},
    )

    # capture structured context from the clarification/about to remember
    _update_context(session_id, frame, out, assessment, question)

    # persist escalations for the admin dashboard
    if out.get("escalation"):
        esc = out["escalation"]
        memory.save_escalation(
            {
                "escalation_id": esc.escalation_id,
                "user_id": user["username"],
                "question": question,
                "summary": esc.summary,
                "reason": esc.reason,
                "docs_ids": esc.docs_ids,
                "passages": esc.passages,
                "created_at": esc.created_at,
                "status": esc.status,
            }
        )

    memory.log_turn(session_id, user["username"], question, status, decision, out.get("citations", []))

    dt_total = (time.time() - t_start) * 1000.0
    print(f"\033[92m🏁 [API-PERF] POST /api/chat COMPLETE in {dt_total:.1f}ms ({dt_total/1000.0:.2f}s)\033[0m\n", flush=True)

    return {
        "session_id": session_id,
        "decision": decision,
        "status": status,
        "answer": out.get("answer", ""),
        "clarification": out.get("clarification", ""),
        "citations": out.get("citations", []),
        "warnings": assessment.warnings if assessment else [],
        "escalation_id": out["escalation"].escalation_id if out.get("escalation") else None,
        "context": _context_diff(frame, session_id),
    }


def _update_context(session_id, frame, out, assessment, question) -> None:
    sess = memory.get_session(session_id)
    if not sess:
        return
    ctx = dict(sess.get("context") or {})
    if out.get("understood"):
        u = out["understood"]
        for k in ("topic", "jurisdiction", "department", "employee_type"):
            if u.get(k):
                ctx[k] = u[k]
    memory.update_session_context(session_id, ctx)


def _context_diff(frame, session_id) -> dict:
    sess = memory.get_session(session_id)
    if not sess:
        return {}
    current = sess.get("context") or {}
    return {
        k: v
        for k, v in current.items()
        if v not in ("", None)
    }


from fastapi.responses import StreamingResponse
import json
from llm import stream_chat
from graph.nodes import SYSTEM_GROUNDED, node_understand, node_retrieve, node_assess, node_decide


@router.post("/stream")
def chat_stream(payload: dict, user: dict = Depends(get_optional_user)):
    question = (payload.get("question") or payload.get("message") or "").strip()
    if not question:
        return {"error": "empty message"}

    session_id = payload.get("session_id")
    session = memory.get_session(session_id) if session_id else None
    if not session:
        session = memory.create_session(user["username"])
        session_id = session["session_id"]

    frame = to_frame(user, session_id)
    if session and session.get("context"):
        for k, v in session["context"].items():
            if getattr(frame, k, None) in ("", None) and v:
                setattr(frame, k, v)

    state = {
        "question": question,
        "frame": frame,
        "history": [],
        "retries": 0,
        "decision": None,
        "answer": "",
        "citations": [],
        "clarification": "",
        "escalation": None,
        "evidence": [],
        "understood": {},
        "assessment": None,
        "restricted": False,
        "trace": [],
    }

    state.update(node_understand(state))
    state.update(node_retrieve(state))
    state.update(node_assess(state))
    state.update(node_decide(state))

    evidence = state["assessment"].evidence if state.get("assessment") else []
    citations = [
        {
            "chunk_id": e.chunk_id,
            "title": e.metadata.title,
            "section": e.section,
            "doc_id": e.metadata.document_id,
            "status": e.metadata.status.value,
            "snippet": e.text[:280],
        }
        for e in evidence
    ]

    def event_stream():
        init_payload = {
            "type": "meta",
            "session_id": session_id,
            "status": state["assessment"].status.value if state.get("assessment") else "NONE",
            "decision": state["decision"].value if state.get("decision") else "NONE",
            "citations": citations,
        }
        yield f"data: {json.dumps(init_payload)}\n\n"

        if not evidence:
            yield f"data: {json.dumps({'type': 'token', 'content': 'I could not find sufficient information in the knowledge base to answer this question.'})}\n\n"
            yield f"data: [DONE]\n\n"
            return

        context = "\n\n".join(
            f"[{i}] ({e.metadata.title}, {e.section}, {e.metadata.document_id} v{e.metadata.version})\n{e.text}"
            for i, e in enumerate(evidence)
        )
        messages = [
            {"role": "system", "content": SYSTEM_GROUNDED},
            {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}"},
        ]

        full_answer = []
        for token in stream_chat(messages):
            full_answer.append(token)
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        answer_text = "".join(full_answer)
        memory.add_message(session_id, "user", question)
        memory.add_message(
            session_id,
            "assistant",
            answer_text,
            meta={"status": init_payload["status"], "decision": init_payload["decision"], "citations": citations},
        )
        yield f"data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")