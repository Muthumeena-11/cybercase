
# cases_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection

bp = Blueprint("cases", __name__, template_folder="../templates")

OWNER_NAME = "krithika"  # correct answer for the beginner mission

def ensure_user_scores_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS user_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER DEFAULT 0,
        status TEXT DEFAULT 'not cleared'
    )""")
    conn.commit()
    conn.close()

@bp.route('/')
def index():
    return render_template('cases/index.html')

# 👇 Add this route for Beginner Case
@bp.route('/case1')
def case1_index():
    return render_template('cases/case1_index.html')
@bp.route("/phone")
def phone():
    return render_template('cases/phone.html')

@bp.route("/messages")
def messages():
    return render_template('cases/messages.html')

@bp.route("/check_answer", methods=['POST'])
def check_answer():
    ensure_user_scores_table()
    answer = (request.form.get("answer") or "").strip().lower()
    user_id = session.get("user_id", None)
    conn = get_db_connection()
    c = conn.cursor()
    # initialize row for user if not exists
    if user_id is not None:
        row = c.execute("SELECT id FROM user_scores WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            c.execute("INSERT INTO user_scores (user_id, score, status) VALUES (?, 0, 'not cleared')", (user_id,))
            conn.commit()

    if answer == OWNER_NAME.lower():
        if user_id is not None:
            c.execute("UPDATE user_scores SET score=?, status=? WHERE user_id=?", (100, 'cleared', user_id))
            conn.commit()
        conn.close()
        return redirect(url_for('cases.mission_complete'))
    else:
        session['feedback'] = "Incorrect. Hint: decode the Base64 in messages."
        conn.close()
        return redirect(url_for('cases.index'))

@bp.route("/mission_complete")
def mission_complete():
    ensure_user_scores_table()
    user_id = session.get("user_id", None)
    score, status = 0, 'not cleared'
    if user_id is not None:
        conn = get_db_connection()
        c = conn.cursor()
        row = c.execute("SELECT score, status FROM user_scores WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        if row:
            score, status = row[0], row[1]
    return render_template('cases/mission_complete.html', score=score, status=status)
