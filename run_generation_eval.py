import datetime
import json
import os
import re

from retrieval import get_model, get_connection, hybrid_search
from generation import generate_answer, GENERATION_MODEL

MIN_PAGE = 7
K = 5

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

with open("eval/eval_set.json") as f:
    questions = json.load(f)

model = get_model()
conn = get_connection()

rows = []
for q in questions:
    if q["category"] not in ("diagnostic", "unanswerable"):
        continue

    chunks = hybrid_search(conn, model, q["question"], result_count=K, min_page=MIN_PAGE)
    retrieved = {c["page_number"] for c in chunks}
    answer = generate_answer(q["question"], chunks)

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
    }
    rows.append(row)
    print(f"{q['id']} abstained={abstained} cited={sorted(cited)} valid={row['citations_valid']}")

answerable = [r for r in rows if not r["should_abstain"]]
unanswerable = [r for r in rows if r["should_abstain"]]

print("\n=== GENERATION SUMMARY ===")
print(f"model: {GENERATION_MODEL}")
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
out_path = f"eval/results/generation_{stamp}.json"
with open(out_path, "w") as f:
    json.dump({"model": GENERATION_MODEL, "min_page": MIN_PAGE, "rows": rows}, f, indent=2)
print(f"\nSaved full answers to {out_path}")

conn.close()