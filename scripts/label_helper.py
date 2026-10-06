import json
from retrieval import get_model, get_connection, hybrid_search

model = get_model()
conn = get_connection()

with open("eval/eval_set.json") as f:
    questions = json.load(f)

for q in questions:
    if q["category"] == "diagnostic" and not q["relevant_pages"]:
        print(f"\n{q['id']}: {q['question']}")
        for r in hybrid_search(conn, model, q["question"], top_n=10, result_count=5):
            print(f"   page {r['page_number']}: {r['content'][:90]!r}")

conn.close()