from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from werkzeug.utils import secure_filename
from datetime import datetime

# Import blueprints
from case.cases_routes import bp as cases_bp
from case.case2_routes import case2_bp
from cmd_module.routes import bp as cmd_drills_bp
from quiz.quiz_routes import quiz_bp

from db import get_db_connection

# -------------------------
# App setup
# -------------------------
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "supersecretkey"  # Change this for production

# Register blueprints
app.register_blueprint(cmd_drills_bp, url_prefix="/cmd-drills")
app.register_blueprint(cases_bp, url_prefix="/cases")
app.register_blueprint(case2_bp)  # url_prefix already set in case2_routes.py
app.register_blueprint(quiz_bp)


# Secret + configs
app.secret_key = os.environ.get("CYBERCASE_SECRET", "dev-secret-change-me")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload


# -------------------------
# Routes
# -------------------------

@app.route("/")
def index():
    """Redirect root to login page if not logged in"""
    if session.get("user_id"):
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.")
            return redirect(url_for("signup"))

        hashed = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username or None, email, hashed)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("⚠️ Email already registered! Try logging in.")
            conn.close()
            return redirect(url_for("signup"))

        conn.close()
        flash("✅ Account created! Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user is None:
            flash("⚠️ No account found with that email.")
            return redirect(url_for("login"))

        if check_password_hash(user["password"], password):
            # set session values
            session.clear()
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["user_name"] = user["username"] if user["username"] else None
            return redirect(url_for("home"))
        else:
            # flash("Invalid email or password. Use test@example.com / password123")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("login"))


@app.route("/home")
def home():
    """User dashboard after login"""
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    # Safe defaults
    user_name = user["username"] if user and "username" in user.keys() and user["username"] else "Agent"
    points = user["last_score"] if user and "points" in user.keys() else 0
    badge = user["last_badge"] if user and "badge" in user.keys() else "Newbie"

    return render_template("home.html", user_name=user_name, points=points, badge=badge)


@app.route("/alerts")
def alerts():
    """Threat intel alerts (placeholder)"""
    if not session.get("user_id"):
        return redirect(url_for("login"))

    sample_alerts = [
        {"title": "Suspicious IP 1.2.3.4", "desc": "Reported for scanning"},
        {"title": "Phishing campaign", "desc": "Targets education sector"}
    ]
    return render_template("alerts.html", alerts=sample_alerts)


@app.route("/evidence", methods=["GET", "POST"])
def evidence():
    """Evidence file upload"""
    if not session.get("user_id"):
        return redirect(url_for("login"))

    uploaded_filename = None
    message = None

    if request.method == "POST":
        if "evidence_file" not in request.files:
            flash("No file part")
            return redirect(url_for("evidence"))

        file = request.files["evidence_file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(url_for("evidence"))

        filename = secure_filename(file.filename)
        saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(saved_path)

        uploaded_filename = filename
        message = "File uploaded. (Processing not implemented in demo.)"

    return render_template("evidence.html", uploaded_filename=uploaded_filename, message=message)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve uploaded files (testing only)"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/password_game")
def password_game():
    """Simple strong/weak password game"""
    STRONG_PASSWORDS = [
        "J@ck_2025!", "A9!rT_3k#Z", "M3ena$2048", "S!lver_F0x88", "Kite#Wind_77",
        "C0bAlt!_Nine", "Aur0ra@Sun*", "N!ght_Owl#39", "R1ver$Flow_09", "H@wk-Eye_55",
        "Xy!_93vK#2", "G@laxy-R1ngs_7", "Pyth0n@Flask!", "Djang0_R0cks#", "C0d3C@se_!2",
        "Str0ng&P@ss_01", "Trail#Bl@ze_66", "M00n_L@ke!5", "Gh0st$Guard_33", "S@feK#ey_90"
    ]
    WEAK_PASSWORDS = [
        "12345", "password", "qwerty", "111111", "abc123",
        "iloveyou", "admin", "letmein", "welcome", "sunshine",
        "dragon", "football", "monkey", "login", "princess",
        "qwerty123", "1q2w3e", "000000", "passw0rd", "user"
    ]

    strong = STRONG_PASSWORDS[:]
    weak = WEAK_PASSWORDS[:]
    random.shuffle(strong)
    random.shuffle(weak)

    return render_template("password_index.html", strong_passwords=strong, weak_passwords=weak)


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
