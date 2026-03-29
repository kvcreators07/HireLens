from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import PyPDF2
import re

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🗄️ DATABASE
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
        jobs TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# 🏠 HOME
@app.route("/")
def index():
    return render_template("index.html")

# 🔐 SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (NULL, ?, ?)", (username, password))
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
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
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

# 📊 DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# 🧠 ANALYZE (IMPROVED)
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/login")

    file = request.files["resume"]

    if file.filename == "":
        return "No file selected"

    filepath = os.path.join("uploads", file.filename)
    file.save(filepath)

    text = ""

    # 📄 Extract text
    try:
        pdf = PyPDF2.PdfReader(filepath)
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + " "
    except:
        text = ""

    text = text.lower()

    # 🔥 MASSIVE SKILL DATABASE
    skill_db = [
        "python","java","c++","c","html","css","javascript","react","angular",
        "node","flask","django","sql","mysql","mongodb","firebase",
        "machine learning","deep learning","data analysis","pandas","numpy",
        "excel","power bi","tableau","git","github","linux","aws","docker"
    ]

    skills = []

    # 🔍 EXACT MATCH USING REGEX
    for skill in skill_db:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            skills.append(skill.title())

    # remove duplicates
    skills = list(set(skills))

    # 🎯 SCORE
    score = min(50 + len(skills) * 5, 100)

    # 💼 JOB MATCHING (REAL LOGIC)
    jobs = []

    if any(s in skills for s in ["Python","Flask","Django"]):
        jobs.append("Python Developer")

    if any(s in skills for s in ["Html","Css","Javascript","React","Angular"]):
        jobs.append("Frontend / Web Developer")

    if any(s in skills for s in ["Node","MongoDb","Sql"]):
        jobs.append("Backend Developer")

    if any(s in skills for s in ["Machine Learning","Deep Learning","Pandas","Numpy"]):
        jobs.append("Data Scientist / Analyst")

    if any(s in skills for s in ["Aws","Docker","Linux"]):
        jobs.append("DevOps Engineer")

    if "Java" in skills:
        jobs.append("Java Developer")

    if "C++" in skills:
        jobs.append("Software Engineer")

    # fallback
    if not jobs:
        jobs.append("General IT Role")

    # 💡 Suggestions
    suggestions = []

    if len(skills) < 3:
        suggestions.append("Add more technical skills")

    if "project" not in text:
        suggestions.append("Add Projects section")

    if "experience" not in text:
        suggestions.append("Add Experience section")

    # 💾 SAVE
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO user_data (username, filename, ats_score, skills, jobs)
    VALUES (?, ?, ?, ?, ?)
    """, (
        session["user"],
        file.filename,
        score,
        ", ".join(skills),
        ", ".join(jobs)
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        score=score,
        skills=skills,
        suggestions=suggestions,
        jobs=jobs
    )

# 📊 ADMIN
@app.route("/admin")
def admin():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM user_data")
    data = c.fetchall()
    conn.close()

    return render_template("admin.html", data=data)

# 🚀 RUN
if __name__ == "__main__":
    app.run(debug=True)