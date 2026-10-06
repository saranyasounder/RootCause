import json

LABELS = {
    "q05": [41, 42, 43, 44],      # cooling fan assembly (41-43) + single fan (44)
    "q07": [48, 49, 50, 51],      # NVDIMM-N battery procedures
    "q09": [132, 133, 134],       # power supply unit
    "q10": [72],                  # install memory module
    "q11": [12],                  # blinking amber health indicator
    "q12": [40],                  # remove air shroud
    "q13": [125, 126],            # system battery
    "q14": [53, 54, 55, 59, 60],  # drive carrier + drive in carrier
    "q15": [88, 89],              # expansion card into riser
    "q16": [30, 31],              # safety instructions
}

PATH = "eval/eval_set.json"

with open(PATH) as f:
    questions = json.load(f)

ids = {q["id"] for q in questions}
missing = set(LABELS) - ids
if missing:
    raise SystemExit(f"These IDs are not in {PATH}: {sorted(missing)}")

for q in questions:
    if q["id"] in LABELS:
        q["relevant_pages"] = LABELS[q["id"]]

with open(PATH, "w") as f:
    json.dump(questions, f, indent=2)
    f.write("\n")

print(f"Updated {len(LABELS)} questions. Total in file: {len(questions)}")