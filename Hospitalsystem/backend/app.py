from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------------- DB CONNECTION ----------------
@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')

def get_db():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- DB INITIALIZATION ----------------
def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        phone TEXT,
        symptoms TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queue (
        token_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        department TEXT,
        status TEXT,
        priority INTEGER,
        timestamp TEXT
    )
    ''')

    conn.commit()
    conn.close()

# Call once at startup
init_db()

# ---------------- ROUTES ----------------

@app.route('/register_patient', methods=['POST'])
def register_patient():
    data = request.json

    if not data:
        return jsonify({"error": "Invalid input"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO patients (name, age, phone, symptoms) VALUES (?, ?, ?, ?)",
        (data['name'], data['age'], data['phone'], data['symptoms'])
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Patient registered"})


@app.route('/generate_token', methods=['POST'])
def generate_token():
    data = request.json

    conn = get_db()
    patient = conn.execute(
        "SELECT id FROM patients ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not patient:
        return jsonify({"error": "No patient found"}), 404

    conn.execute(
        "INSERT INTO queue (patient_id, department, status, priority, timestamp) VALUES (?, ?, 'waiting', ?, ?)",
        (patient['id'], data['department'], data.get('priority', 0), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Token generated"})


@app.route('/queue_status', methods=['GET'])
def queue_status():
    conn = get_db()

    queue = conn.execute("""
        SELECT 
            queue.token_id,
            queue.status,
            queue.department,
            patients.name
        FROM queue
        JOIN patients ON queue.patient_id = patients.id
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in queue])


@app.route('/call_next', methods=['POST'])
def call_next():
    conn = get_db()

    patient = conn.execute(
        "SELECT * FROM queue WHERE status='waiting' ORDER BY priority DESC, timestamp LIMIT 1"
    ).fetchone()

    if patient:
        conn.execute(
            "UPDATE queue SET status='in_progress' WHERE token_id=?",
            (patient['token_id'],)
        )
        conn.commit()
        conn.close()
        return jsonify(dict(patient))

    conn.close()
    return jsonify({"message": "No patients in queue"})


@app.route('/complete_patient', methods=['POST'])
def complete_patient():
    data = request.json

    conn = get_db()
    conn.execute(
        "UPDATE queue SET status='completed' WHERE token_id=?",
        (data['token_id'],)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Patient marked as completed"})
@app.route('/complete_current', methods=['POST'])
def complete_current():
    conn = get_db()

    patient = conn.execute(
        "SELECT * FROM queue WHERE status='in_progress' LIMIT 1"
    ).fetchone()

    if patient:
        conn.execute(
            "UPDATE queue SET status='completed' WHERE token_id=?",
            (patient['token_id'],)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Patient completed"})

    conn.close()
    return jsonify({"message": "No active patient"})

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    print("[INFO] Server running at http://127.0.0.1:5000")
    app.run(debug=True)