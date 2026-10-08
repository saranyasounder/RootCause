# Equipment Support Copilot (RootCause)

A retrieval-augmented support assistant for equipment troubleshooting. It routes each question to the right backend (an exact SQL lookup for error codes, or hybrid semantic + keyword retrieval over a real hardware manual), answers with page-level citations, and ships with an evaluation harness that measures routing, retrieval and answer quality.

The evaluation is the point of the project: every design choice below was measured, and the failures are documented.

## Architecture

```
question
   |
   v
 router  --- explicit error code / known equipment ID? ---> SQL lookup (error_codes table)
   |
   | open-ended question
   v
 hybrid retrieval (pgvector cosine + Postgres full-text, fused with RRF)
   |   front matter excluded (pages 1-6)
   v
 neighbor expansion (+/- 1 chunk around each hit)
   |
   v
 Claude Haiku 4.5, answers ONLY from excerpts, cites [page N], refuses if unsupported
```

**Stack:** FastAPI, PostgreSQL 17 + pgvector, sentence-transformers (`all-MiniLM-L6-v2`, 384-dim), Anthropic API.

**Data:** the Dell PowerEdge R740 Installation and Service Manual (155 pages, chunked per page at 1000 characters with 150 overlap), plus a **synthetic** equipment/error-code/ticket dataset (10 units, 75 error codes) generated for this project. The manual PDF is not included in this repo.

## Results

### Evaluation set

28 hand-written questions: 9 error-code lookups, 11 diagnostic questions about the manual, 4 ambiguous routing cases, and 4 questions the manual cannot answer. Relevant pages for each diagnostic question were verified by hand against the PDF. Two labels (q05, q07) were widened after that verification showed several valid procedures; I note this because it changes those questions' precision scores.

### Routing

| Metric | Result |
|---|---|
| Path accuracy | 26/28 (92.9%) |
| Code + equipment extraction (structured questions) | 10/11 |

Both failures are known limitations: `F1010` with no dash (q04) and a negated code, "this is *not* an F-1010 error" (q17).

### Retrieval (11 diagnostic questions, page-level)

| Configuration | P@5 | hit@5 | MRR |
|---|---|---|---|
| Semantic only | 0.582 | 1.000 | 0.848 |
| Semantic, front matter excluded | 0.582 | 1.000 | 0.864 |
| Hybrid (RRF) | 0.545 | 1.000 | 0.927 |
| Hybrid, front matter excluded | 0.545 | 1.000 | 0.932 |

Every method found a relevant page in the top 5 for every question. Hybrid ranked the first relevant page higher (MRR) but returned slightly more near-miss neighbors (P@5). With 11 questions the difference between methods is within noise; I don't claim either is better. Excluding the table of contents removed TOC chunks from results but changed scores only slightly.

### Generation (LLM-judged, one run per configuration)

Answers were graded by a separate model (Claude Sonnet 5.5) for outcome (answered / partial / refused) and faithfulness (every claim supported by the excerpts shown).

| | Baseline (top 5 chunks) | + neighbor expansion |
|---|---|---|
| Answerable: answered | 8/11 | 11/11 |
| Answerable: faithful | 7/11 | 9/11 |
| Unanswerable: correctly refused | 4/4 | 4/4 |

**What neighbor expansion fixed.** For "How do I remove the cooling shroud?" the baseline refused. The manual page was split across two chunks, and the chunk holding the removal steps (chunk 111) never reached the model. I confirmed this directly from the saved context: chunk 111 was absent in the baseline and present with expansion, and the answer became correct. The cost: context grew from 5 to 13 chunks per question (about 2.6x the input tokens).

**What I don't claim.** These are single runs, and I could not fix the sampling temperature on these models, so outputs vary between runs (in repeated baseline runs, only 7 of 15 answers were byte-identical, though citations and refusals mostly matched). The unanswerable-faithfulness difference between configurations reflects whether the model happened to append "consult the vendor" advice on that run, not the effect of expansion.

## Known limitations

- **Router:** no negation handling, no dashless codes (`F1010`). Regex plus substring matching, no learned component.
- **Refusals add unsupported advice** ("contact Dell sales"). The judge counts this as unfaithful under the excerpts-only rule. A prompt change could address it; I have not tested one.
- **Incomplete answers:** for q06 the model said a light "can mean one of two things" when the page lists three patterns.
- **Vocabulary mismatch:** the manual says "air shroud", users may say "cooling shroud". Retrieval coped here, but only one such case is tested.
- **Small, single-manual scope:** 28 questions, one manual, synthetic tickets and error codes. Page-level labels are a coarse proxy for relevance.
- **Judge is an LLM.** [I audited N verdicts by hand and agreed with M. Fill in after checking.]
- **Migration note:** page numbers were initially stored 0-indexed and corrected with a one-time `UPDATE` (+1); `scripts/load_manual.py` now stores 1-indexed pages.

## Run it

```
conda create -n equipment-copilot python=3.11 && conda activate equipment-copilot
python -m pip install -r requirements.txt
createdb equipment_copilot
psql equipment_copilot -f schema.sql          # creates tables (pgvector required)
# place the manual at manuals/dell_manual.pdf, then, from the project root:
python scripts/generate_error_codes.py
python scripts/load_error_codes.py
python scripts/generate_tickets.py
python scripts/load_manual.py
python scripts/embed_data.py
# .env must contain ANTHROPIC_API_KEY=...
python -m uvicorn main:app --reload
```

```
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "How do I remove the cooling shroud?"}'
```

## Reproduce the evaluation

```
python run_eval.py                         # routing + retrieval (no API calls)
python run_generation_eval.py [--expand]   # generate answers, save to eval/results/
python run_judge.py                        # grade the latest generation run
```

Results from my runs are in `eval/results/`.