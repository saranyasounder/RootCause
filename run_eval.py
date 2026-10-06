import json
from retrieval import get_model, get_connection, semantic_search, hybrid_search
from router import route_question

K = 5
CONTENT_START = 7  # pages 1-6 are cover, notes and table of contents

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
# 2. Retrieval: semantic vs hybrid, with and without front matter
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


def get_pages(method, min_page, question):
    if method == "semantic":
        rows = semantic_search(conn, model, question, top_n=K, min_page=min_page)
        return [row[1] for row in rows]
    results = hybrid_search(conn, model, question, top_n=10, result_count=K, min_page=min_page)
    return [r["page_number"] for r in results]


CONFIGS = [
    ("semantic", 1),
    ("semantic", CONTENT_START),
    ("hybrid", 1),
    ("hybrid", CONTENT_START),
]

scored = [q for q in questions if q["category"] == "diagnostic" and q["relevant_pages"]]
totals = {cfg: {"p": [], "hit": [], "rr": []} for cfg in CONFIGS}

for q in scored:
    relevant = set(q["relevant_pages"])
    print(f"{q['id']} relevant={sorted(relevant)}")
    for cfg in CONFIGS:
        method, min_page = cfg
        pages = get_pages(method, min_page, q["question"])
        totals[cfg]["p"].append(precision_at_k(pages, relevant))
        totals[cfg]["hit"].append(hit_at_k(pages, relevant))
        totals[cfg]["rr"].append(reciprocal_rank(pages, relevant))
        print(f"   {method:<8} min_page={min_page}: {pages}")

n = len(scored)
print(f"\nOver {n} questions:")
print(f"   {'config':<26} {'P@' + str(K):>7} {'hit@' + str(K):>7} {'MRR':>7}")
for cfg in CONFIGS:
    method, min_page = cfg
    label = f"{method}, min_page={min_page}"
    t = totals[cfg]
    print(f"   {label:<26} {sum(t['p'])/n:>7.3f} {sum(t['hit'])/n:>7.3f} {sum(t['rr'])/n:>7.3f}")

conn.close()