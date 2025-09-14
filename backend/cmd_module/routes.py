# cmd_module/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, g, flash
import sqlite3, os

bp = Blueprint("cmd_drills", __name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "challenges.db")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

@bp.route("/")
def index():
    db = get_db()
    cur = db.execute("SELECT id, title, description FROM levels ORDER BY id")
    levels = cur.fetchall()
    return render_template("cmd_drills/index.html", levels=levels)

@bp.route("/level/<int:level_id>", methods=["GET", "POST"])
def level(level_id):
    db = get_db()
    cur = db.execute("SELECT * FROM levels WHERE id = ?", (level_id,))
    level = cur.fetchone()
    if not level:
        flash("Level not found.", "danger")
        return redirect(url_for('cmd_drills.index'))

    attempts = int(request.cookies.get(f"attempts_{level_id}", "0"))
    hint_unlocked = attempts >= 2

    if request.method == "POST":
        cmd = request.form.get("command", "").strip()
        normalized = " ".join(cmd.split())
        solution = level["solution"].strip()
        if normalized == solution:
            resp = redirect(url_for("cmd_drills.success", level_id=level_id))
            resp.set_cookie(f"cleared_{level_id}", "1", max_age=60*60*24*365)
            resp.set_cookie(f"attempts_{level_id}", "0", max_age=0)
            return resp
        else:
            attempts += 1
            flash("Incorrect command. Try again.", "warning")
            resp = redirect(url_for("cmd_drills.level", level_id=level_id))
            resp.set_cookie(f"attempts_{level_id}", str(attempts), max_age=60*60)
            return resp

    return render_template("cmd_drills/level.html", level=level, attempts=attempts, hint_unlocked=hint_unlocked)

@bp.route("/success/<int:level_id>")
def success(level_id):
    db = get_db()
    cur = db.execute("SELECT id, title FROM levels WHERE id = ?", (level_id,))
    level = cur.fetchone()
    if not level:
        flash("Level not found.", "danger")
        return redirect(url_for('cmd_drills.index'))
    return render_template("cmd_drills/success.html", level=level)

