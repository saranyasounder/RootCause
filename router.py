import re
import psycopg2

ERROR_CODE_PATTERN = re.compile(r"\b[A-Z]-\d{4}\b")


def extract_error_code(question):
    match = ERROR_CODE_PATTERN.search(question.upper())
    return match.group(0) if match else None


def get_known_equipment_ids(conn):
    """Fetch all real equipment IDs from the database."""
    cur = conn.cursor()
    cur.execute("SELECT equipment_id FROM equipment")
    return [row[0] for row in cur.fetchall()]


def extract_equipment_id(question, known_ids):
    """Return the first known equipment ID found in the question, or None."""
    question_upper = question.upper()
    for equipment_id in known_ids:
        if equipment_id.upper() in question_upper:
            return equipment_id
    return None


def structured_lookup(conn, error_code, equipment_id=None):
    """
    Direct SQL lookup for a known error code, joined with equipment info.
    If equipment_id is given, scope the results to that one unit.
    """
    cur = conn.cursor()
    if equipment_id:
        cur.execute(
            """
            SELECT e.equipment_id, e.model, e.equipment_type,
                   ec.error_code, ec.error_description, ec.severity,
                   ec.typical_cause, ec.recommended_action
            FROM error_codes ec
            JOIN equipment e ON e.equipment_id = ec.equipment_id
            WHERE ec.error_code = %s AND ec.equipment_id = %s
            """,
            (error_code, equipment_id),
        )
    else:
        cur.execute(
            """
            SELECT e.equipment_id, e.model, e.equipment_type,
                   ec.error_code, ec.error_description, ec.severity,
                   ec.typical_cause, ec.recommended_action
            FROM error_codes ec
            JOIN equipment e ON e.equipment_id = ec.equipment_id
            WHERE ec.error_code = %s
            """,
            (error_code,),
        )
    return cur.fetchall()


def route_question(conn, question):
    error_code = extract_error_code(question)

    if error_code:
        known_ids = get_known_equipment_ids(conn)
        equipment_id = extract_equipment_id(question, known_ids)

        rows = structured_lookup(conn, error_code, equipment_id)
        if rows:
            return {
                "path": "structured",
                "error_code": error_code,
                "equipment_id": equipment_id,
                "results": rows,
            }
        else:
            return {
                "path": "structured",
                "error_code": error_code,
                "equipment_id": equipment_id,
                "results": [],
                "note": f"Error code {error_code} was mentioned but not found"
                        + (f" for equipment {equipment_id}" if equipment_id else "") + ".",
            }

    return {"path": "semantic", "results": None}