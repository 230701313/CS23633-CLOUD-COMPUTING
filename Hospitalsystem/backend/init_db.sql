CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    phone TEXT,
    symptoms TEXT
);

CREATE TABLE queue (
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    department TEXT,
    status TEXT,
    priority INTEGER,
    timestamp TEXT
);
