import json

NEW = [
    {
        "id": "q23",
        "question": "What does error S-3005 mean on SVR-R740-02?",
        "expected_error_code": "S-3005",
        "expected_equipment_id": "SVR-R740-02",
    },
    {
        "id": "q24",
        "question": "SVR-R650-01 is reporting W-4501. What is the recommended action?",
        "expected_error_code": "W-4501",
        "expected_equipment_id": "SVR-R650-01",
    },
    {
        "id": "q25",
        "question": "How do I fix error V-6009 on LAP-LAT5540-01?",
        "expected_error_code": "V-6009",
        "expected_equipment_id": "LAP-LAT5540-01",
    },
    {
        "id": "q26",
        "question": "What is error P-4017?",
        "expected_error_code": "P-4017",
        "expected_equipment_id": None,
    },
    {
        "id": "q27",
        "question": "What is the cause of F-1035 on LAP-LAT5540-02?",
        "expected_error_code": "F-1035",
        "expected_equipment_id": "LAP-LAT5540-02",
    },
    {
        "id": "q28",
        "question": "WKS-T5820-02 is showing F-1022. How severe is it?",
        "expected_error_code": "F-1022",
        "expected_equipment_id": "WKS-T5820-02",
    },
]

PATH = "eval/eval_set.json"

with open(PATH) as f:
    questions = json.load(f)

existing = {q["id"] for q in questions}
added = 0
for item in NEW:
    if item["id"] in existing:
        continue
    questions.append({
        "id": item["id"],
        "question": item["question"],
        "category": "lookup",
        "expected_path": "structured",
        "expected_error_code": item["expected_error_code"],
        "expected_equipment_id": item["expected_equipment_id"],
        "relevant_pages": [],
        "should_abstain": False,
    })
    added += 1

# q18 was written against SVR-R740-01, but F-1010 exists on SVR-R740-02
for q in questions:
    if q["id"] == "q18":
        q["expected_equipment_id"] = "SVR-R740-02"
        q["question"] = "what does f-1010 mean on SVR-R740-02?"

with open(PATH, "w") as f:
    json.dump(questions, f, indent=2)
    f.write("\n")

print(f"Added {added} lookups. Total in file: {len(questions)}")