import re
from sentence_transformers import SentenceTransformer
import psycopg2
from pgvector.psycopg2 import register_vector

RRF_K = 60


def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def get_connection():
    conn = psycopg2.connect(dbname="equipment_copilot")
    register_vector(conn)
    return conn


def build_or_query(text):
    words = re.findall(r"\w+", text.lower())
    return " | ".join(words) if words else None


def semantic_search(conn, model, query_text, top_n=10, min_page=1):
    query_embedding = model.encode(query_text)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, page_number, content
        FROM chunks
        WHERE page_number >= %s
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        (min_page, query_embedding, top_n),
    )
    return cur.fetchall()


def keyword_search(conn, query_text, top_n=10, min_page=1):
    keyword_query_str = build_or_query(query_text)
    if keyword_query_str is None:
        return []
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, page_number, content
        FROM chunks
        WHERE to_tsvector('english', content) @@ to_tsquery('english', %s)
          AND page_number >= %s
        ORDER BY ts_rank(to_tsvector('english', content), to_tsquery('english', %s)) DESC
        LIMIT %s
        """,
        (keyword_query_str, min_page, keyword_query_str, top_n),
    )
    return cur.fetchall()


def hybrid_search(conn, model, query_text, top_n=10, result_count=5, min_page=1):
    semantic_results = semantic_search(conn, model, query_text, top_n, min_page)
    keyword_results = keyword_search(conn, query_text, top_n, min_page)

    scores = {}
    chunk_lookup = {}

    for rank, (chunk_id, page_number, content) in enumerate(semantic_results):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank + 1)
        chunk_lookup[chunk_id] = (page_number, content)

    for rank, (chunk_id, page_number, content) in enumerate(keyword_results):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank + 1)
        chunk_lookup[chunk_id] = (page_number, content)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for chunk_id, score in ranked[:result_count]:
        page_number, content = chunk_lookup[chunk_id]
        results.append({
            "id": chunk_id,
            "page_number": page_number,
            "content": content,
            "score": score,
        })
    return results

def expand_with_neighbors(conn, results, window=1, min_page=1):
    """For each hit, also include the chunks `window` positions before and after it.

    Keeps hits in rank order, adds each hit's neighbors in document order, and
    drops duplicates. Neighbors are marked is_hit=False.
    """
    cur = conn.cursor()
    seen = set()
    expanded = []

    for hit in results:
        cur.execute(
            """
            SELECT c2.id, c2.page_number, c2.content
            FROM chunks c1
            JOIN chunks c2
              ON c2.document_id = c1.document_id
             AND c2.chunk_index BETWEEN c1.chunk_index - %s AND c1.chunk_index + %s
            WHERE c1.id = %s
            ORDER BY c2.chunk_index
            """,
            (window, window, hit["id"]),
        )
        for chunk_id, page_number, content in cur.fetchall():
            if chunk_id in seen or page_number < min_page:
                continue
            seen.add(chunk_id)
            expanded.append({
                "id": chunk_id,
                "page_number": page_number,
                "content": content,
                "score": hit["score"],
                "is_hit": chunk_id == hit["id"],
            })
    return expanded