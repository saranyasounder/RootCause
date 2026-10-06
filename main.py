from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2

from retrieval import get_model, get_connection, hybrid_search
from router import route_question
from generation import generate_answer

app = FastAPI(title="Equipment Support Copilot")

# Load the embedding model once at startup, not per-request
model = get_model()


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(request: AskRequest):
    conn = get_connection()
    try:
        routing_result = route_question(conn, request.question)

        if routing_result["path"] == "structured":
            return {
                "path": "structured",
                "error_code": routing_result["error_code"],
                "equipment_id": routing_result.get("equipment_id"),
                "results": [
                    {
                        "equipment_id": row[0],
                        "model": row[1],
                        "equipment_type": row[2],
                        "error_code": row[3],
                        "description": row[4],
                        "severity": row[5],
                        "typical_cause": row[6],
                        "recommended_action": row[7],
                    }
                    for row in routing_result["results"]
                ],
                "note": routing_result.get("note"),
            }

        else:
            chunks = hybrid_search(conn, model, request.question, min_page=7)
            answer = generate_answer(request.question, chunks)
            return {
                "path": "semantic",
                "answer": answer,
                "sources": [
                    {"page_number": c["page_number"], "score": c["score"]}
                    for c in chunks
                ],
            }

    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}