import re
from sentence_transformers import SentenceTransformer
import psycopg2
from pgvector.psycopg2 import register_vector

model = SentenceTransformer("all-MiniLM-L6-v2")

conn = psycopg2.connect(dbname="equipment_copilot")
register_vector(conn)
cur = conn.cursor()

query_text = "the wireless syncing thing on the front panel won't connect to my phone"
query_embedding = model.encode(query_text)

TOP_N = 10
RRF_K = 60


def build_or_query(text):
    words = re.findall(r"\w+", text.lower())
    return " | ".join(words) if words else None


# --- Semantic search: top N by vector distance ---
cur.execute(
    "SELECT id, page_number, content FROM chunks ORDER BY embedding <=> %s LIMIT %s",
    (query_embedding, TOP_N),
)
semantic_results = cur.fetchall()

# --- Keyword search: OR across all query words, ranked by relevance ---
keyword_query_str = build_or_query(query_text)

cur.execute(
    """
    SELECT id, page_number, content
    FROM chunks
    WHERE to_tsvector('english', content) @@ to_tsquery('english', %s)
    ORDER BY ts_rank(to_tsvector('english', content), to_tsquery('english', %s)) DESC
    LIMIT %s
    """,
    (keyword_query_str, keyword_query_str, TOP_N),
)
keyword_results = cur.fetchall()

print(f"Semantic matches: {len(semantic_results)}")
print(f"Keyword matches: {len(keyword_results)}")

print("\n--- Semantic-only top 3 ---")
for chunk_id, page_number, content in semantic_results[:3]:
    print(f"[page {page_number}]", content[:120].replace("\n", " "))

# --- Combine via Reciprocal Rank Fusion ---
scores = {}
chunk_lookup = {}

for rank, (chunk_id, page_number, content) in enumerate(semantic_results):
    scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank + 1)
    chunk_lookup[chunk_id] = (page_number, content)

for rank, (chunk_id, page_number, content) in enumerate(keyword_results):
    scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank + 1)
    chunk_lookup[chunk_id] = (page_number, content)

ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

print("\n--- Hybrid (RRF) top 3 ---")
for chunk_id, score in ranked[:3]:
    page_number, content = chunk_lookup[chunk_id]
    print(f"[page {page_number}] score={score:.5f}", content[:120].replace("\n", " "))

cur.close()
conn.close()