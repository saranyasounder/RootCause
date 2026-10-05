import json
from retrieval import get_model, get_connection, semantic_search, hybrid_search
from router import route_question

K = 5

with open("eval/eval_set.json") as f:
    questions = json.load(f)

model = get_model()
conn = get_connection()

# ---------------------------------------------------------------
# 1. Routing accuracy
# ---------------------------------------------------------------
print("=== ROUTING ===")
path_correct = 0
structured_expected = 0
extraction_correct = 0

for q in questions:
    result = route_question(conn, q["question"])
    path_ok = result["path"] == q["expected_path"]
    path_correct += path_ok

    line = f"{q['id']} [{q['category']}] path={result['path']} (expected {q['expected_path']})"

    if q["expected_path"] == "structured":
        structured_expected += 1
        code_ok = result.get("error_code") == q["expected_error_code"]
        equip_ok = result.get("equipment_id") == q["expected_equipment_id"]
        extraction_correct += (path_ok and code_ok and equip_ok)
        line += f" code_ok={code_ok} equip_ok={equip_ok}"

    print(("PASS " if path_ok else "FAIL ") + line)

print(f"\nRouting accuracy: {path_correct}/{len(questions)} = {path_correct / len(questions):.1%}")
print(f"Extraction accuracy (structured questions): {extraction_correct}/{structured_expected}")

# ---------------------------------------------------------------
# 2. Retrieval precision@K: semantic-only vs hybrid
# ---------------------------------------------------------------
print("\n=== RETRIEVAL ===")


def precision_at_k(pages, relevant):
    return sum(p in relevant for p in pages) / len(pages)


scored = [q for q in questions if q["category"] == "diagnostic" and q["relevant_pages"]]
sem_scores, hyb_scores = [], []

for q in scored:
    relevant = set(q["relevant_pages"])
    sem_pages = [row[1] for row in semantic_search(conn, model, q["question"], top_n=K)]
    hyb_pages = [r["page_number"] for r in hybrid_search(conn, model, q["question"], top_n=10, result_count=K)]

    sem_p = precision_at_k(sem_pages, relevant)
    hyb_p = precision_at_k(hyb_pages, relevant)
    sem_scores.append(sem_p)
    hyb_scores.append(hyb_p)

    print(f"{q['id']} relevant={sorted(relevant)}")
    print(f"   semantic pages={sem_pages}  P@{K}={sem_p:.2f}")
    print(f"   hybrid   pages={hyb_pages}  P@{K}={hyb_p:.2f}")

print(f"\nMean P@{K} over {len(scored)} questions:")
print(f"   semantic-only: {sum(sem_scores) / len(scored):.3f}")
print(f"   hybrid (RRF):  {sum(hyb_scores) / len(scored):.3f}")

conn.close()