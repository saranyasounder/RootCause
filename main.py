import anthropic
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from generation import generate_answer
from retrieval import get_model, get_connection, hybrid_search, expand_with_neighbors
from router import route_question

MIN_PAGE = 7  # pages 1-6 are cover, notes and table of contents

app = FastAPI(title="Equipment Support Copilot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
model = get_model()


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(request: AskRequest):
    conn = get_connection()
    try:
        routed = route_question(conn, request.question)

        if routed["path"] == "structured":
            fields = [
                "equipment_id", "model", "equipment_type", "error_code",
                "error_description", "severity", "typical_cause", "recommended_action",
                ]
            return {**routed, "results": [dict(zip(fields, row)) for row in routed["results"]]}

        chunks = hybrid_search(conn, model, request.question, min_page=MIN_PAGE)
        chunks = expand_with_neighbors(conn, chunks, window=1, min_page=MIN_PAGE)
        sources = [
            {"page_number": c["page_number"], "score": c["score"], "is_hit": c["is_hit"]}
            for c in chunks
        ]

        try:
            answer = generate_answer(request.question, chunks)
        except anthropic.APIError as e:
            return {
                "path": "semantic",
                "answer": None,
                "error": f"Answer generation unavailable ({type(e).__name__}).",
                "sources": sources,
            }

        return {"path": "semantic", "answer": answer, "sources": sources}
    finally:
        conn.close()