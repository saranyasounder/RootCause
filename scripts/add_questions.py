import json

NEW = [
    # --- ambiguous routing: "expected_path" is what a CORRECT router should do ---
    {
        "id": "q17",
        "question": "This is not an F-1010 error, the fan is just very loud. What should I check?",
        "category": "ambiguous",
        "expected_path": "semantic",
        "expected_error_code": None,
        "expected_equipment_id": None,
        "relevant_pages": [],
        "should_abstain": False,
    },
    {
        "id": "q18",
        "question": "what does f-1010 mean on SVR-R740-01?",
        "category": "ambiguous",
        "expected_path": "structured",
        "expected_error_code": "F-1010",
        "expected_equipment_id": "SVR-R740-01",
        "relevant_pages": [],
        "should_abstain": False,
    },
    {
        "id": "q19",
        "question": "Tell me about SVR-R740-01",
        "category": "ambiguous",
        "expected_path": "semantic",
        "expected_error_code": None,
        "expected_equipment_id": None,
        "relevant_pages": [],
        "should_abstain": False,
    },
    # --- unanswerable from the manual ---
    {
        "id": "q20",
        "question": "How much does a replacement power supply cost?",
        "category": "unanswerable",
        "expected_path": "semantic",
        "expected_error_code": None,
        "expected_equipment_id": None,
        "relevant_pages": [],
        "should_abstain": True,
    },
    {
        "id": "q21",
        "question": "How do I configure a VLAN on a Cisco switch?",
        "category": "unanswerable",
        "expected_path": "semantic",
        "expected_error_code": None,
        "expected_equipment_id": None,
        "relevant_pages": [],
        "should_abstain": True,
    },
    {
        "id": "q22",
        "question": "Which Linux distribution does Dell recommend for this server?",
        "category": "unanswerable",
        "expected_path": "semantic",
        "expected_error_code": None,
        "expected_equipment_id": None,
        "relevant_pages": [],
        "should_abstain": True,
    },
]

PATH = "eval/eval_set.json"

with open(PATH) as f:
    questions = json.load(f)

existing = {q["id"] for q in questions}
added = [q for q in NEW if q["id"] not in existing]
questions.extend(added)

with open(PATH, "w") as f:
    json.dump(questions, f, indent=2)
    f.write("\n")

print(f"Added {len(added)} questions. Total in file: {len(questions)}")