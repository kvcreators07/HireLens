from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import PyPDF2
import re
import random

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        filename TEXT,
        ats_score INTEGER,
        skills TEXT,
        jobs TEXT,
        applied_job TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (NULL, ?, ?)", (u,p))
        conn.commit()
        conn.close()
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = u
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM user_data WHERE username=?", (session["user"],))
    data = c.fetchall()
    conn.close()

    return render_template("dashboard.html", data=data)

# ---------------- ANALYZE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/login")

    file = request.files["resume"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    text = ""
    try:
        pdf = PyPDF2.PdfReader(filepath)
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text()
    except:
        text = ""

    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9 ]', ' ', text)

    # -------- SKILLS --------
    skill_db = [
        "python","java","c++","html","css","javascript","react",
        "sql","machine learning","data analysis","seo","content writing"
    ]

    skills = []
    for skill in skill_db:
        if skill in text:
            skills.append(skill)

    # -------- SCORE --------
    score = len(skills)*6 + random.randint(40,60)
    if score > 95:
        score = 95

    # -------- JOBS --------
    jobs = []
    if "python" in skills:
        jobs.append("Python Developer")
    if "html" in skills or "css" in skills:
        jobs.append("Web Developer")
    if "seo" in skills:
        jobs.append("SEO Specialist")
    if "content writing" in skills:
        jobs.append("Content Writer")

    if not jobs:
        jobs.append("General Role")

    # -------- SAVE --------
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    INSERT INTO user_data (username, filename, ats_score, skills, jobs)
    VALUES (?, ?, ?, ?, ?)
    """,(session["user"], file.filename, score, ", ".join(skills), ", ".join(jobs)))

    conn.commit()
    conn.close()

    return render_template("result.html", score=score, skills=skills, jobs=jobs)

# -------- APPLY --------
@app.route("/apply/<job>")
def apply(job):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("UPDATE user_data SET applied_job=? WHERE username=?",
              (job, session["user"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------- RECRUITER --------
@app.route("/recruiter")
def recruiter():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM user_data")
    data = c.fetchall()
    conn.close()

    return render_template("recruiter.html", data=data)

@app.route("/update/<int:id>/<status>")
def update(id, status):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE user_data SET status=? WHERE id=?", (status,id))
    conn.commit()
    conn.close()

    return redirect("/recruiter")

# -------- ADMIN --------
@app.route("/admin")
def admin():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM user_data")
    data = c.fetchall()
    conn.close()

    return render_template("admin.html", data=data)

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)