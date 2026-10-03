
DROP TABLE IF EXISTS error_codes CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;


CREATE TABLE equipment (
    equipment_ID TEXT PRIMARY KEY, --unique identifier for each piece of equipment
    model TEXT NOT NULL,
    equipment_type TEXT NOT NULL

);

CREATE TABLE error_codes (
    id SERIAL PRIMARY KEY,
    equipment_id TEXT NOT NULL REFERENCES equipment(equipment_id),
    error_code TEXT NOT NULL,
    category TEXT NOT NULL,
    error_description TEXT NOT NULL,
    severity TEXT NOT NULL,
    typical_cause TEXT NOT NULL,
    recommended_action TEXT NOT NULL
);

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    equipment_id TEXT NOT NULL REFERENCES equipment(equipment_id),
    error_code TEXT,
    ticket_date DATE NOT NULL,
    severity TEXT NOT NULL,
    resolved_status TEXT NOT NULL,
    tickets_description TEXT NOT NULL
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    source_file TEXT NOT NULL
);

CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL
);