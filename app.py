from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from PyPDF2 import PdfReader

if not os.path.exists("uploads"):
    os.makedirs("uploads")

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 🗄️ DATABASE INIT
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
    conn.commit()
    conn.close()

init_db()

# 🌐 HOME
@app.route("/")
def home():
    return render_template("index.html")

# 🔐 SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# 🔐 LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html")

# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# 📊 DASHBOARD (UPLOAD PAGE)
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# 🧠 RESUME ANALYSIS FUNCTION
def analyze_resume(text):
    SKILLS_DB = ["python", "java", "html", "css", "javascript",
                 "react", "sql", "seo", "content writing", "communication"]

    text = text.lower()

    # 🔹 Skills
    found_skills = [skill for skill in SKILLS_DB if skill in text]

    # 🔹 ATS Score
    score = min(len(found_skills) * 10, 100)

    # 🔹 Suggestions
    suggestions = []
    if score < 50:
        suggestions.append("Add more relevant skills")
    if "projects" not in text:
        suggestions.append("Include projects section")
    if "experience" not in text:
        suggestions.append("Add work experience")

    # 🔹 Job Mapping
    JOB_MAP = {
        "python": ["Python Developer", "Data Analyst"],
        "java": ["Java Developer"],
        "html": ["Web Developer"],
        "css": ["Frontend Developer"],
        "javascript": ["Frontend Developer"],
        "react": ["React Developer"],
        "sql": ["Database Administrator"],
        "seo": ["SEO Specialist"],
        "content writing": ["Content Writer"],
        "communication": ["HR", "Customer Support"]
    }

    jobs = set()
    for skill in found_skills:
        if skill in JOB_MAP:
            jobs.update(JOB_MAP[skill])

    return found_skills, score, suggestions, list(jobs)

# 📂 ANALYZE ROUTE
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/login")

    file = request.files["resume"]

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # 📄 Read PDF
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    skills, score, suggestions, jobs = analyze_resume(text)

    return render_template("result.html",
                           skills=skills,
                           score=score,
                           suggestions=suggestions,
                           jobs=jobs)

# ▶️ RUN APP
if __name__ == "__main__":
    app.run(debug=True)