import glob
import json
import sys


def load(path):
    data = json.load(open(path))
    return data, {r["id"]: r for r in data["rows"]}


if len(sys.argv) == 3:
    path_a, path_b = sys.argv[1], sys.argv[2]
else:
    files = sorted(glob.glob("eval/results/generation_*.json"))
    path_a, path_b = files[-2], files[-1]

meta_a, a = load(path_a)
meta_b, b = load(path_b)

print(f"A: {path_a}  (expand={meta_a.get('expand')})")
print(f"B: {path_b}  (expand={meta_b.get('expand')})\n")

diffs = 0
for qid in a:
    if qid not in b:
        continue
    ra, rb = a[qid], b[qid]
    same_pages = ra["cited_pages"] == rb["cited_pages"]
    same_abstain = ra["abstained"] == rb["abstained"]
    same_text = ra["answer"] == rb["answer"]
    if not (same_pages and same_abstain):
        diffs += 1
        print(f"{qid}: cited {ra['cited_pages']} -> {rb['cited_pages']}, "
              f"abstained {ra['abstained']} -> {rb['abstained']}")
    elif not same_text:
        print(f"{qid}: same citations and abstention, wording differs")

identical = sum(a[q]["answer"] == b[q]["answer"] for q in a if q in b)
print(f"\nQuestions with different citations or abstention: {diffs}")
print(f"Questions with byte-identical answers: {identical}/{len(a)}")