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

def hit_at_k(pages, relevant):
    return 1.0 if any(p in relevant for p in pages) else 0.0


def reciprocal_rank(pages, relevant):
    for i, p in enumerate(pages, start=1):
        if p in relevant:
            return 1.0 / i
    return 0.0


scored = [q for q in questions if q["category"] == "diagnostic" and q["relevant_pages"]]
sem_scores, hyb_scores = [], []
sem_hits, hyb_hits = [], []
sem_rr, hyb_rr = [], []

for q in scored:
    relevant = set(q["relevant_pages"])
    sem_pages = [row[1] for row in semantic_search(conn, model, q["question"], top_n=K)]
    hyb_pages = [r["page_number"] for r in hybrid_search(conn, model, q["question"], top_n=10, result_count=K)]

    sem_p = precision_at_k(sem_pages, relevant)
    hyb_p = precision_at_k(hyb_pages, relevant)
    sem_hits.append(hit_at_k(sem_pages, relevant))
    hyb_hits.append(hit_at_k(hyb_pages, relevant))
    sem_rr.append(reciprocal_rank(sem_pages, relevant))
    hyb_rr.append(reciprocal_rank(hyb_pages, relevant))
    sem_scores.append(sem_p)
    hyb_scores.append(hyb_p)

    print(f"{q['id']} relevant={sorted(relevant)}")
    print(f"   semantic pages={sem_pages}  P@{K}={sem_p:.2f}")
    print(f"   hybrid   pages={hyb_pages}  P@{K}={hyb_p:.2f}")

n = len(scored)
print(f"\nOver {n} questions:")
print(f"   {'metric':<10} {'semantic':>10} {'hybrid':>10}")
print(f"   {'P@' + str(K):<10} {sum(sem_scores)/n:>10.3f} {sum(hyb_scores)/n:>10.3f}")
print(f"   {'hit@' + str(K):<10} {sum(sem_hits)/n:>10.3f} {sum(hyb_hits)/n:>10.3f}")
print(f"   {'MRR':<10} {sum(sem_rr)/n:>10.3f} {sum(hyb_rr)/n:>10.3f}")

conn.close()