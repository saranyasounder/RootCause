from retrieval import get_model, get_connection, hybrid_search

model = get_model()
conn = get_connection()

results = hybrid_search(conn, model, "the wireless syncing thing on the front panel won't connect to my phone")

for r in results:
    print(f"[page {r['page_number']}] score={r['score']:.5f}")
    print(r["content"][:120].replace("\n", " "))
    print()