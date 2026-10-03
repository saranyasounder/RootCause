from sentence_transformers import SentenceTransformer
import psycopg2
from pgvector.psycopg2 import register_vector

model = SentenceTransformer("all-MiniLM-L6-v2")

conn = psycopg2.connect(dbname="equipment_copilot")
register_vector(conn)
cur = conn.cursor()

query = "device sounds like a jet engine and keeps overheating"
query_embedding = model.encode(query)

cur.execute(
    """
    SELECT id, page_number, content, embedding <=> %s AS distance
    FROM chunks
    ORDER BY distance
    LIMIT 5
    """,
    (query_embedding,),
)

for row in cur.fetchall():
    print(f"[page {row[1]}] distance={row[3]:.4f}")
    print(row[2][:200].replace("\n", " "))
    print()

cur.close()
conn.close()