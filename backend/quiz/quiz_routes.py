from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, g
import sqlite3, os, json, random, datetime

# Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database.db"))
QUESTION_BANK = os.path.join(BASE_DIR, "question_bank.json")

quiz_bp = Blueprint("quiz", __name__, template_folder="../templates/quiz", static_folder="../static/quiz")

# --- DB Helpers ---
def get_db():
    if "quiz_db" not in g:
        g.quiz_db = sqlite3.connect(DB_PATH)
        g.quiz_db.row_factory = sqlite3.Row
    return g.quiz_db

@quiz_bp.teardown_request
def close_db(exception):
    db = g.pop("quiz_db", None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Users table
    # cur.execute('''CREATE TABLE IF NOT EXISTS users (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     username TEXT UNIQUE,
    #     user_name TEXT,
    #     last_score INTEGER DEFAULT 0,
    #     last_badge TEXT,
    #     last_attempt_time TEXT,
    #     last_questions TEXT
    # )''')
    # Attempts table
    cur.execute('''CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        total INTEGER,
        time TEXT,
        question_ids TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# --- Load Questions ---
def load_questions():
    with open(QUESTION_BANK, "r") as f:
        return json.load(f)

# --- Routes ---
@quiz_bp.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("quiz/quiz.html")

@quiz_bp.route("/quiz/start", methods=["POST"])
def start_quiz():
    if "user_id" not in session:
        return jsonify({"error": "not_logged_in"}), 403

    user_id = session["user_id"]
    questions = load_questions()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT last_questions FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    last_qs = []
    if row and row["last_questions"]:
        try:
            last_qs = json.loads(row["last_questions"])
        except:
            last_qs = []

    # Pick 8 random questions
    pool = [q for q in questions if q["id"] not in last_qs]
    if len(pool) < 8:
        pool = questions[:]
    chosen = random.sample(pool, 8)

    # Save question IDs in session
    session["current_question_ids"] = [q["id"] for q in chosen]

    # Don’t send answers to frontend
    for q in chosen:
        q.pop("answer", None)

    return jsonify({"questions": chosen, "timer": 90})

@quiz_bp.route("/quiz/submit", methods=["POST"])
def submit():
    if "user_id" not in session:
        return redirect(url_for("index"))

    data = request.json
    answers = data.get("answers", {})
    question_ids = session.get("current_question_ids", [])
    all_questions = load_questions()
    qmap = {q["id"]: q for q in all_questions}

    score = 0
    total = len(question_ids)
    correct_questions = []
    wrong_questions = []

    for qid in question_ids:
        qid = int(qid)
        correct = qmap[qid]["answer"]
        selected = answers.get(str(qid), None)
        if selected is not None and int(selected) == int(correct):
            score += 1
            correct_questions.append(qmap[qid]["question"])
        else:
            wrong_questions.append(qmap[qid]["question"])

    # Badge logic
    badge = "Keep Practicing"
    if score == total:
        badge = "Cyber Hero"
    elif score >= total * 0.75:
        badge = "Cyber Defender"
    elif score >= total * 0.5:
        badge = "Cyber Learner"

    # Save to DB
    conn = get_db()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO attempts (user_id, score, total, time, question_ids) VALUES (?,?,?,?,?)",
        (session["user_id"], score, total, now, json.dumps(question_ids)),
    )
    cur.execute(
        "UPDATE users SET last_score=?, last_badge=?, last_attempt_time=?, last_questions=? WHERE id=?",
        (score, badge, now, json.dumps(question_ids), session["user_id"]),
    )
    conn.commit()

    # Clean up
    session.pop("current_question_ids", None)

    result = {
        "score": score,
        "total": total,
        "badge": badge,
        "correct": correct_questions,
        "wrong": wrong_questions,
    }
    return jsonify(result)

@quiz_bp.route("/quiz/leaderboard")
def leaderboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, last_score, last_badge, last_attempt_time FROM users "
        "ORDER BY last_score DESC, last_attempt_time ASC LIMIT 20"
    )
    rows = [dict(x) for x in cur.fetchall()]
    return render_template("quiz/leaderboard.html", leaderboard=rows)
