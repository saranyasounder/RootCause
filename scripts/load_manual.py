from pypdf import PdfReader
import psycopg2

DOCUMENT_ID = 1
CHUNK_SIZE = 1000       # target characters per chunk
CHUNK_OVERLAP = 150     # characters repeated between consecutive chunks
MIN_PAGE_CHARS = 50     # skip near-empty pages (blank separators, etc.)


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


reader = PdfReader("manuals/dell_manual.pdf")

conn = psycopg2.connect(dbname="equipment_copilot")
cur = conn.cursor()

chunk_index = 0
total_chunks = 0

for page_num, page in enumerate(reader.pages):
    text = page.extract_text()
    if len(text.strip()) < MIN_PAGE_CHARS:
        continue  # skip near-empty pages

    for piece in chunk_text(text):
        cur.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, content, page_number)
            VALUES (%s, %s, %s, %s)
            """,
            (DOCUMENT_ID, chunk_index, piece, page_num),
        )
        chunk_index += 1
        total_chunks += 1

conn.commit()
cur.close()
conn.close()

print(f"Inserted {total_chunks} chunks from {len(reader.pages)} pages.")