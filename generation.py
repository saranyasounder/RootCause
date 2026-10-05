import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

GENERATION_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")

SYSTEM_PROMPT = """You are a technical support assistant for equipment maintenance.
Answer the user's question using ONLY the provided manual excerpts below.
Every claim in your answer must be traceable to one of the excerpts.
Cite the page number for each claim using the format [page N].
If the excerpts do not contain enough information to answer the question,
say so clearly instead of guessing."""


def build_context(chunks):
    """Format retrieved chunks into a labeled context block for the prompt."""
    parts = []
    for chunk in chunks:
        parts.append(f"[page {chunk['page_number']}]\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def generate_answer(question, chunks):
    """Given a question and retrieved chunks, generate a grounded, cited answer."""
    context = build_context(chunks)

    user_message = f"""Manual excerpts:

{context}

---

Question: {question}"""

    response = client.chat.completions.create(
        model=GENERATION_MODEL,
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content