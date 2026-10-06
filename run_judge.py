import glob
import json
import os
import re
import sys
import time

import anthropic
from dotenv import load_dotenv

from generation import build_context

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "claude-sonnet-5-5")

JUDGE_SYSTEM = """You are grading an answer written by a technical-support assistant that was only allowed to use the provided manual excerpts.

You will be given the excerpts, the question, and the assistant's answer. Grade two things.

1. outcome:
   - "answered": the answer gives the information the question asks for.
   - "partial": the answer gives some of the requested information and says other needed information is missing.
   - "refused": the answer declines to give the requested information (a refusal may still point the user elsewhere).
2. faithful: true only if EVERY factual claim and instruction in the answer is supported by the excerpts. Advice, steps or facts that do not appear in the excerpts (general knowledge, suggestions to check other documents the excerpts do not mention) count as unsupported.

Also list:
- unsupported_claims: each unsupported claim, quoted briefly.
- miscited: claims cited to a page whose excerpt does not support them.

Respond with ONLY a JSON object with keys: outcome, faithful, unsupported_claims, miscited, explanation (one sentence)."""


def call_judge(question, context_text, answer, attempts=4, wait=30):
    user = f"""Excerpts:

{context_text}

---

Question: {question}

---

Answer to grade:

{answer}"""
    for attempt in range(1, attempts + 1):
        try:
            response = client.messages.create(
                model=JUDGE_MODEL,
                max_tokens=4000,
                system=JUDGE_SYSTEM,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(b.text for b in response.content if b.type == "text")
        except anthropic.APIStatusError as e:
            if e.status_code in (429, 500, 502, 503, 529) and attempt < attempts:
                print(f"   API error {e.status_code}; waiting {wait}s")
                time.sleep(wait)
            else:
                raise


def parse_json(text):
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = sorted(glob.glob("eval/results/generation_*.json"))[-1]

data = json.load(open(path))
print(f"Judging {path}  (expand={data.get('expand')}, judge={JUDGE_MODEL})\n")

judged = []
for row in data["rows"]:
    if "context" not in row:
        raise SystemExit("This results file has no saved context. Rerun run_generation_eval.py first.")
    context_text = build_context(row["context"])
    raw = call_judge(row["question"], context_text, row["answer"])
    verdict = parse_json(raw)
    if verdict is None:
        print(f"{row['id']}: could not parse judge output, skipping")
        continue
    judged.append({**row, "judge": verdict})
    flag = "" if verdict["faithful"] else "  <-- UNFAITHFUL"
    print(f"{row['id']} outcome={verdict['outcome']} faithful={verdict['faithful']}{flag}")

answerable = [r for r in judged if not r["should_abstain"]]
unanswerable = [r for r in judged if r["should_abstain"]]

print("\n=== JUDGE SUMMARY ===")
print(f"answer file: {path}")
if answerable:
    n = len(answerable)
    for label in ("answered", "partial", "refused"):
        count = sum(r["judge"]["outcome"] == label for r in answerable)
        print(f"   answerable -> {label:<9} {count}/{n}")
    print(f"   answerable -> faithful  {sum(r['judge']['faithful'] for r in answerable)}/{n}")
if unanswerable:
    m = len(unanswerable)
    print(f"   unanswerable -> refused  {sum(r['judge']['outcome'] == 'refused' for r in unanswerable)}/{m}")
    print(f"   unanswerable -> faithful {sum(r['judge']['faithful'] for r in unanswerable)}/{m}")

print("\n=== PROBLEMS ===")
for r in judged:
    v = r["judge"]
    if not v["faithful"] or v.get("miscited"):
        print(f"{r['id']}: {v['explanation']}")
        for c in v.get("unsupported_claims", []):
            print(f"     unsupported: {c}")
        for c in v.get("miscited", []):
            print(f"     miscited:    {c}")

os.makedirs("eval/results", exist_ok=True)
out_path = os.path.join("eval/results", "judged_" + os.path.basename(path))
with open(out_path, "w") as f:
    json.dump({"source": path, "judge_model": JUDGE_MODEL, "rows": judged}, f, indent=2)
print(f"\nSaved judged results to {out_path}")