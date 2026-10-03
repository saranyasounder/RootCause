import csv
import psycopg2

EQUIPMENT_TYPE_BY_PREFIX = {
    "SVR": "server",
    "WKS": "workstation",
    "LAP": "laptop",
    "TAPE": "tape",
    "NAS": "storage",
    "FAB": "fab_tool",
}


def infer_equipment_type(equipment_id: str) -> str:
    prefix = equipment_id.split("-")[0]
    return EQUIPMENT_TYPE_BY_PREFIX.get(prefix, "unknown")


conn = psycopg2.connect(dbname="equipment_copilot")
cur = conn.cursor()

with open("data/error_codes.csv", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# --- Insert equipment first, since error_codes references it ---
seen_equipment = {}
for row in rows:
    seen_equipment[row["equipment_id"]] = row["model"]

for equipment_id, model in seen_equipment.items():
    cur.execute(
        """
        INSERT INTO equipment (equipment_id, model, equipment_type)
        VALUES (%s, %s, %s)
        ON CONFLICT (equipment_id) DO NOTHING
        """,
        (equipment_id, model, infer_equipment_type(equipment_id)),
    )

# --- Now insert the error codes ---
for row in rows:
    cur.execute(
        """
        INSERT INTO error_codes
            (equipment_id, error_code, category, error_description,
             severity, typical_cause, recommended_action)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            row["equipment_id"],
            row["error_code"],
            row["category"],
            row["description"],
            row["severity"],
            row["typical_cause"],
            row["recommended_action"],
        ),
    )

conn.commit()
cur.close()
conn.close()

print(f"Loaded {len(seen_equipment)} equipment records and {len(rows)} error codes.")