import glob
import json

latest = sorted(glob.glob("eval/results/generation_*.json"))[-1]
results = json.load(open(latest))
questions = {q["id"]: q for q in json.load(open("eval/eval_set.json"))}

precisions = []
for row in results["rows"]:
    if row["should_abstain"] or not row["cited_pages"]:
        continue
    relevant = set(questions[row["id"]]["relevant_pages"])
    cited = set(row["cited_pages"])
    p = len(cited & relevant) / len(cited)
    precisions.append(p)
    print(f"{row['id']} cited={sorted(cited)} relevant={sorted(relevant)} precision={p:.2f}")

print(f"\nFile: {latest}")
print(f"Mean citation precision: {sum(precisions) / len(precisions):.3f} over {len(precisions)} answers")