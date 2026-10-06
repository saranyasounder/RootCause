import datetime
import json
import os
import re
import sys
import time

import anthropic

from retrieval import get_model, get_connection, hybrid_search, expand_with_neighbors
from generation import generate_answer, GENERATION_MODEL

MIN_PAGE = 7
K = 5
EXPAND = "--expand" in sys.argv

ABSTAIN_PHRASES = [
    "do not contain",
    "does not contain",
    "not contain enough",
    "not enough information",
    "do not provide",
    "does not provide",
    "no information",
    "cannot answer",
    "not covered",
    "not mentioned",
]


def generate_with_retry(question, chunks, attempts=4, wait=30):
    for attempt in range(1, attempts + 1):
        try:
            return generate_answer(question, chunks)
        except anthropic.APIStatusError as e:
            if e.status_code in (429, 500, 502, 503, 529) and attempt < attempts:
                print(f"   API error {e.status_code}; waiting {wait}s (attempt {attempt}/{attempts})")
                time.sleep(wait)
            else:
                raise


with open("eval/eval_set.json") as f:
    questions = json.load(f)

model = get_model()
conn = get_connection()

print(f"Neighbor expansion: {'ON' if EXPAND else 'OFF'}")

rows = []
for q in questions:
    if q["category"] not in ("diagnostic", "unanswerable"):
        continue

    chunks = hybrid_search(conn, model, q["question"], result_count=K, min_page=MIN_PAGE)
    if EXPAND:
        chunks = expand_with_neighbors(conn, chunks, window=1, min_page=MIN_PAGE)

    retrieved = {c["page_number"] for c in chunks}
    answer = generate_with_retry(q["question"], chunks)

    groups = re.findall(r"\[[^\]]*?page[^\]]*?\]", answer, re.I)
    cited = {int(n) for g in groups for n in re.findall(r"\d+", g)}

    relevant = set(q["relevant_pages"])
    abstained = any(p in answer.lower() for p in ABSTAIN_PHRASES)

    row = {
        "id": q["id"],
        "question": q["question"],
        "should_abstain": q["should_abstain"],
        "abstained": abstained,
        "cited_pages": sorted(cited),
        "retrieved_pages": sorted(retrieved),
        "has_citation": bool(cited),
        "citations_valid": cited <= retrieved,
        "cites_relevant_page": bool(cited & relevant),
        "answer": answer,
        "context": [
            {"id": c["id"], "page_number": c["page_number"], "content": c["content"]}
            for c in chunks
        ],
    }
    rows.append(row)
    print(f"{q['id']} abstained={abstained} cited={sorted(cited)} valid={row['citations_valid']}")

answerable = [r for r in rows if not r["should_abstain"]]
unanswerable = [r for r in rows if r["should_abstain"]]

print("\n=== GENERATION SUMMARY ===")
print(f"model: {GENERATION_MODEL}")
print(f"neighbor expansion: {'ON' if EXPAND else 'OFF'}")
if answerable:
    n = len(answerable)
    print(f"Answerable ({n}):")
    print(f"   has citation:          {sum(r['has_citation'] for r in answerable)}/{n}")
    print(f"   all citations valid:   {sum(r['citations_valid'] for r in answerable)}/{n}")
    print(f"   cites a relevant page: {sum(r['cites_relevant_page'] for r in answerable)}/{n}")
    print(f"   wrongly abstained:     {sum(r['abstained'] for r in answerable)}/{n}")
if unanswerable:
    m = len(unanswerable)
    print(f"Unanswerable ({m}):")
    print(f"   correctly abstained:   {sum(r['abstained'] for r in unanswerable)}/{m}")

os.makedirs("eval/results", exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = f"eval/results/generation_{stamp}{'_expand' if EXPAND else ''}.json"
with open(out_path, "w") as f:
    json.dump(
        {
            "model": GENERATION_MODEL,
            "min_page": MIN_PAGE,
            "expand": EXPAND,
            "temperature": 0,
            "rows": rows,
        },
        f,
        indent=2,
    )
print(f"\nSaved full answers to {out_path}")

conn.close()