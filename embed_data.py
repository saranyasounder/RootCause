from sentence_transformers import SentenceTransformer
import psycopg2
from pgvector.psycopg2 import register_vector

model = SentenceTransformer("all-MiniLM-L6-v2")

conn = psycopg2.connect(dbname="equipment_copilot")
register_vector(conn)
cur = conn.cursor()

# --- Embed chunks ---
cur.execute("SELECT id, content FROM chunks")
rows = cur.fetchall()
ids = [r[0] for r in rows]
texts = [r[1] for r in rows]

print(f"Embedding {len(texts)} chunks...")
embeddings = model.encode(texts, show_progress_bar=True)

for id_, emb in zip(ids, embeddings):
    cur.execute("UPDATE chunks SET embedding = %s WHERE id = %s", (emb, id_))
conn.commit()

# --- Embed tickets ---
cur.execute("SELECT id, tickets_description FROM tickets")
rows = cur.fetchall()
ids = [r[0] for r in rows]
texts = [r[1] for r in rows]

print(f"Embedding {len(texts)} tickets...")
embeddings = model.encode(texts, show_progress_bar=True)

for id_, emb in zip(ids, embeddings):
    cur.execute("UPDATE tickets SET embedding = %s WHERE id = %s", (emb, id_))
conn.commit()

cur.close()
conn.close()
print("Done.")