import psycopg2
from router import route_question

conn = psycopg2.connect(dbname="equipment_copilot")

test_questions = [
    "What does error F-1010 mean?",
    "SVR-R740-01 threw error C-2001, what's going on?",
    "My tool keeps overheating and sounds like a jet engine",
    "What is error Z-9999?",  # doesn't exist
    "My F-1010 error is on a different unit, not SVR-R740-01",
]

for q in test_questions:
    result = route_question(conn, q)
    print(f"Q: {q}")
    print(f"  -> path: {result['path']}")
    if result["path"] == "structured":
        print(f"  -> error_code: {result['error_code']}")
        print(f"  -> results found: {len(result['results'])}")
        if result["results"]:
            print(f"  -> {result['results'][0]}")
    print()

conn.close()