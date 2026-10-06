import glob
import json

runs = {"baseline": [], "expansion": []}

for path in sorted(glob.glob("eval/results/judged_*.json")):
    data = json.load(open(path))
    config = "expansion" if "_expand" in data["source"] else "baseline"
    rows = data["rows"]
    answerable = [r for r in rows if not r["should_abstain"]]
    unanswerable = [r for r in rows if r["should_abstain"]]
    runs[config].append({
        "file": path,
        "answered": sum(r["judge"]["outcome"] == "answered" for r in answerable),
        "faithful": sum(r["judge"]["faithful"] for r in answerable),
        "n_answerable": len(answerable),
        "refused": sum(r["judge"]["outcome"] == "refused" for r in unanswerable),
        "unans_faithful": sum(r["judge"]["faithful"] for r in unanswerable),
        "n_unanswerable": len(unanswerable),
    })

for config, items in runs.items():
    print(f"\n=== {config} ({len(items)} runs) ===")
    for it in items:
        print(f"   answered {it['answered']}/{it['n_answerable']}  "
              f"faithful {it['faithful']}/{it['n_answerable']}  "
              f"refused {it['refused']}/{it['n_unanswerable']}  "
              f"unans-faithful {it['unans_faithful']}/{it['n_unanswerable']}   {it['file'][-34:]}")
    if items:
        k = len(items)
        for key in ("answered", "faithful", "refused", "unans_faithful"):
            vals = [it[key] for it in items]
            print(f"   {key:<15} mean {sum(vals)/k:.1f}  range {min(vals)}-{max(vals)}")