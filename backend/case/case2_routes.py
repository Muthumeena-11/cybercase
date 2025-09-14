from flask import Blueprint, render_template, g, request, redirect, url_for, flash
import os, sqlite3, datetime, base64, json

# Blueprint setup
case2_bp = Blueprint("case2", __name__, url_prefix="/case2")

# Database path (inside this case's folder)
APP_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(APP_DIR, "usb_case.db")

# -------------------- DB Helpers --------------------
def get_db():
    """Return a per-request SQLite connection with Row dict-like access."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@case2_bp.teardown_app_request
def close_connection(exc):
    """Close db connection after each request (only for this blueprint)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Create tables and seed demo data if db is empty."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    c = db.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY,
        name TEXT, type TEXT, size INTEGER,
        is_hidden INTEGER DEFAULT 0,
        author TEXT, modified TEXT, notes TEXT,
        is_malware INTEGER DEFAULT 0,
        contains_sensitive INTEGER DEFAULT 0,
        content TEXT,
        path TEXT,
        parent_id INTEGER REFERENCES files(id)
    );
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, val TEXT);
    """)

    cur = c.execute("SELECT COUNT(*) AS n FROM files")
    if cur.fetchone()["n"] == 0:
        now = datetime.datetime(2025, 8, 22, 10, 0, 0).isoformat()
        # Seed root files
        files = [
            dict(name="MeetingNotes.docx", type="docx", size=24, author="HR Department", modified=now,
                 notes="Weekly sync notes.", content="Agenda:\n- Hiring pipeline\n- Security awareness session\n- Lunch & Learn",
                 is_hidden=0, is_malware=0, contains_sensitive=0, path=None, parent_id=None),
            dict(name="ProjectBudget.xlsx", type="xlsx", size=88, author="Admin", modified=now, notes="FY25 budget outline",
                 content="", is_hidden=0, is_malware=0, contains_sensitive=0, path=None, parent_id=None),
            dict(name="Photos.zip", type="zip", size=512, author="Unknown", modified=now, notes="Compressed holiday photos",
                 content="", is_hidden=0, is_malware=0, contains_sensitive=0, path=None, parent_id=None),
            dict(name="readme.txt", type="txt", size=2, author="Unknown", modified=now, notes="Plain text readme",
                 content="If found, please return to the front desk.", is_hidden=0, is_malware=0, contains_sensitive=0,
                 path=None, parent_id=None),
            dict(name="report.pdf", type="pdf", size=140, author="Unknown", modified=now, notes="Quarterly CSR report",
                 content="", is_hidden=0, is_malware=0, contains_sensitive=0, path=None, parent_id=None),
            dict(name="Invoice.pdf.exe", type="exe", size=620, author="—", modified=now,
                 notes="Looks like a PDF, but it's an executable.", content="", is_hidden=0, is_malware=1,
                 contains_sensitive=0, path=None, parent_id=None),
            dict(name="confidential.txt", type="txt", size=4, author="—", modified=now, notes="Hidden file",
                 content="Top Secret Client List:\n- Acme Corp\n- Globex Inc\n- Initech\n[Leak Detected]",
                 is_hidden=1, is_malware=0, contains_sensitive=1, path=None, parent_id=None),
        ]
        c.executemany("""
            INSERT INTO files(name,type,size,author,modified,notes,content,is_hidden,is_malware,contains_sensitive,path,parent_id)
            VALUES(:name,:type,:size,:author,:modified,:notes,:content,:is_hidden,:is_malware,:contains_sensitive,:path,:parent_id)
        """, files)

        # Photos.zip children
        parent_id = c.execute("SELECT id FROM files WHERE name='Photos.zip'").fetchone()["id"]
        images = [
            dict(name="beach.jpg", type="img", size=220, author="Camera", modified=now, notes="", content="",
                 is_hidden=0, is_malware=0, contains_sensitive=0, path="images/beach.jpg", parent_id=parent_id),
            dict(name="mountain.jpg", type="img", size=240, author="Camera", modified=now, notes="", content="",
                 is_hidden=0, is_malware=0, contains_sensitive=0, path="images/mountain.jpg", parent_id=parent_id),
            dict(name="city.jpg", type="img", size=200, author="Camera", modified=now, notes="Check EXIF", content="",
                 is_hidden=0, is_malware=0, contains_sensitive=0, path="images/city.jpg", parent_id=parent_id),
        ]
        c.executemany("""
            INSERT INTO files(name,type,size,author,modified,notes,content,is_hidden,is_malware,contains_sensitive,path,parent_id)
            VALUES(:name,:type,:size,:author,:modified,:notes,:content,:is_hidden,:is_malware,:contains_sensitive,:path,:parent_id)
        """, images)

        # Fake EXIF data
        secret = "Flag{USB_CASE_INTERMEDIATE}"
        b64 = base64.b64encode(secret.encode()).decode()
        c.execute("INSERT OR REPLACE INTO settings(key,val) VALUES('exif_city', ?)", (json.dumps({
            "Make": "CYBERCAM 1.0",
            "Model": "Sim-EXIF",
            "HiddenMessage": "true",
            "UserComment": b64,
            "Software": "PhotoDesk 3.2"
        }),))
        db.commit()
    db.close()

# -------------------- Routes --------------------
@case2_bp.before_app_request
def ensure_db():
    """Initialize DB on first request (lazy creation)."""
    init_db()

@case2_bp.route("/start")
def start():
    show_hidden = request.args.get("show_hidden", "0")
    db = get_db()
    query = "SELECT * FROM files WHERE parent_id IS NULL"
    if show_hidden != "1":
        query += " AND is_hidden=0"
    files = db.execute(query + " ORDER BY name").fetchall()
    return render_template("case2/index.html", files=files, show_hidden=show_hidden)

@case2_bp.route("/file/<int:file_id>")
def file_page(file_id):
    show_hidden = request.args.get("show_hidden", "0")
    db = get_db()
    file = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    if not file:
        flash("File not found", "danger")
        return redirect(url_for("case2.start"))
    return render_template("case2/file.html", file=file, show_hidden=show_hidden)

@case2_bp.route("/properties/<int:file_id>")
def properties(file_id):
    show_hidden = request.args.get("show_hidden", "0")
    db = get_db()
    file = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    if not file:
        flash("File not found", "danger")
        return redirect(url_for("case2.start"))

    exif = None
    if file["name"] == "city.jpg":
        raw = db.execute("SELECT val FROM settings WHERE key='exif_city'").fetchone()
        if raw:
            exif = json.loads(raw["val"])
    return render_template("case2/properties.html", file=file, exif=exif, show_hidden=show_hidden)

@case2_bp.route("/extract/<int:file_id>")
def extract_zip(file_id):
    show_hidden = request.args.get("show_hidden", "0")
    db = get_db()
    parent = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    if not parent or parent["type"] != "zip":
        flash("Not a zip file.", "danger")
        return redirect(url_for("case2.start"))
    subfiles = db.execute("SELECT * FROM files WHERE parent_id=? ORDER BY name", (file_id,)).fetchall()
    return render_template("case2/zip.html", parent=parent, subfiles=subfiles, show_hidden=show_hidden)

@case2_bp.route("/assessment", methods=["GET", "POST"])
def assessment():
    show_hidden = request.args.get("show_hidden", "0")
    db = get_db()
    files = db.execute("SELECT * FROM files WHERE parent_id IS NULL ORDER BY name").fetchall()

    if request.method == "POST":
        malware_id = request.form.get("malware_id") or ""
        sensitive_id = request.form.get("sensitive_id") or ""
        exif_hint = (request.form.get("exif_hint") or "").strip()

        mal = db.execute("SELECT * FROM files WHERE id=?", (malware_id,)).fetchone() if malware_id else None
        sen = db.execute("SELECT * FROM files WHERE id=?", (sensitive_id,)).fetchone() if sensitive_id else None

        correct_mal = db.execute("SELECT id FROM files WHERE name='Invoice.pdf.exe'").fetchone()["id"]
        correct_sen = db.execute("SELECT id FROM files WHERE name='confidential.txt'").fetchone()["id"]
        secret = "Flag{USB_CASE_INTERMEDIATE}"

        score, messages = 0, []

        if mal and mal["id"] == correct_mal:
            score += 1
            messages.append("<b>Malware:</b> Correct — double extension executable.")
        else:
            messages.append("<b>Malware:</b> Incorrect. Look for a double extension like <code>.pdf.exe</code>.")

        if sen and sen["id"] == correct_sen:
            score += 1
            messages.append("<b>Sensitive data:</b> Correct — hidden file revealed by Show Hidden.")
        else:
            messages.append("<b>Sensitive data:</b> Incorrect. Hidden files can hide leaks.")

        if exif_hint:
            if exif_hint == secret:
                score += 1
                messages.append(f"<b>EXIF phrase:</b> Correct — {secret}")
            else:
                messages.append("<b>EXIF phrase:</b> Not matching. Inspect EXIF of <code>city.jpg</code> (UserComment is encoded).")
        else:
            messages.append("<b>EXIF phrase:</b> (optional) Decode Base64 from image properties.")

        if score == 3:
            flash(f"✅ Case solved! All findings are correct.<br><code>{secret}</code>", "success")
        else:
            flash(f"Partial score: {score}/3<br>{'<br>'.join(messages)}", "warn")
        return redirect(url_for("case2.assessment", show_hidden=show_hidden))

    return render_template("case2/assessment.html", files=files, show_hidden=show_hidden)
