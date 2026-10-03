import random
from datetime import date, timedelta
import psycopg2

random.seed(7)

conn = psycopg2.connect(dbname="equipment_copilot")
cur = conn.cursor()

# --- Pull real equipment + error code combos out of the database ---
cur.execute("""
    SELECT e.equipment_id, e.model, ec.error_code, ec.error_description, ec.severity
    FROM equipment e
    JOIN error_codes ec ON e.equipment_id = ec.equipment_id
""")
known_faults = cur.fetchall()  # list of tuples

RESOLVED_STATUSES = ["resolved", "resolved", "resolved", "open", "escalated"]

TEMPLATES_WITH_CODE = [
    "Engineer reported {model} ({equipment_id}) throwing error {error_code}. {description}",
    "Ticket opened after {equipment_id} logged {error_code} during routine check. {description}",
    "{model} unit {equipment_id} flagged {error_code}; field tech dispatched.",
]

TEMPLATES_NO_CODE = [
    "{model} ({equipment_id}) reported acting up, no specific error code captured yet.",
    "User noted unusual behavior on {equipment_id}; investigating before code is confirmed.",
    "Intermittent issue reported on {equipment_id}, not yet reproduced or coded.",
]


def random_date():
    start = date(2025, 1, 1)
    days_range = (date.today() - start).days
    return start + timedelta(days=random.randint(0, days_range))


tickets = []

# Ticket type 1: tied to a known error code (most common case)
for _ in range(50):
    equipment_id, model, error_code, description, severity = random.choice(known_faults)
    template = random.choice(TEMPLATES_WITH_CODE)
    text = template.format(
        model=model, equipment_id=equipment_id,
        error_code=error_code, description=description,
    )
    tickets.append((equipment_id, error_code, random_date(), severity,
                     random.choice(RESOLVED_STATUSES), text))

# Ticket type 2: vague report, no error code yet (realistic — not everything is diagnosed)
for _ in range(15):
    equipment_id, model, _, _, severity = random.choice(known_faults)
    template = random.choice(TEMPLATES_NO_CODE)
    text = template.format(model=model, equipment_id=equipment_id)
    tickets.append((equipment_id, None, random_date(), severity,
                     random.choice(RESOLVED_STATUSES), text))

for equipment_id, error_code, ticket_date, severity, resolved_status, description in tickets:
    cur.execute(
        """
        INSERT INTO tickets (equipment_id, error_code, ticket_date, severity, resolved_status, tickets_description)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (equipment_id, error_code, ticket_date, severity, resolved_status, description),
    )

conn.commit()
cur.close()
conn.close()

print(f"Loaded {len(tickets)} tickets ({50} with error codes, {15} without).")