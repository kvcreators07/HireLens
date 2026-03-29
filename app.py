from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import PyPDF2
import re

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
        jobs TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (NULL, ?, ?)", (u, p))
        conn.commit()
        conn.close()

        return redirect("/login")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = u
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# ---------------- ANALYZE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/login")

    file = request.files["resume"]

    if file.filename == "":
        return "No file selected"

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    text = ""

    # PDF extraction
    try:
        pdf = PyPDF2.PdfReader(filepath)
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + " "
    except:
        text = ""

    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9 ]', ' ', text)

    # -------- SKILL DATABASE --------
    skill_db = {
        "Python":["python"], "Java":["java"], "C++":["c++","cpp"],
        "HTML":["html"], "CSS":["css"], "JavaScript":["javascript"],
        "React":["react"], "Angular":["angular"], "Node.js":["node"],
        "Flask":["flask"], "Django":["django"],
        "SQL":["sql"], "MySQL":["mysql"], "MongoDB":["mongodb"],
        "Machine Learning":["machine learning"], "Data Analysis":["analysis"],
        "Pandas":["pandas"], "NumPy":["numpy"],
        "Git":["git"], "GitHub":["github"], "Docker":["docker"],
        "AWS":["aws"], "Linux":["linux"],

        # CONTENT
        "Content Writing":["content writing"],
        "Blog Writing":["blog writing"],
        "Copywriting":["copywriting"],
        "SEO":["seo","keyword"],
        "Proofreading":["proofreading"],
        "Editing":["editing"],
        "Research":["research"],
        "AI Writing":["chatgpt"],

        # TOOLS
        "Excel":["excel"], "Power BI":["power bi"], "Tableau":["tableau"],

        # SOFT
        "Communication":["communication"],
        "Leadership":["leadership"],
        "Teamwork":["teamwork"]
    }

    skills = []

    for skill, keywords in skill_db.items():
        for word in keywords:
            if word in text:
                skills.append(skill)
                break

    skills = list(set(skills))

    # -------- SCORE --------
   score = 0

# 🔹 Skills weight
score += len(skills) * 10

# 🔹 Sections weight
if "education" in text:
    score += 10

if "experience" in text:
    score += 15

if "project" in text:
    score += 15

# 🔹 Bonus for advanced skills
if any(s in skills for s in ["Python","Machine Learning","Data Analysis"]):
    score += 10

# 🔹 Content profiles ke liye
if any(s in skills for s in ["Content Writing","SEO","Copywriting"]):
    score += 10

# 🔹 Limit
if score > 100:
    score = 100

# 🔹 Minimum fallback
if score < 30:
    score = 35

    # -------- JOBS --------
    jobs = []

    if any(s in skills for s in ["Python","Flask","Django"]):
        jobs.append("Python Developer")

    if any(s in skills for s in ["HTML","CSS","JavaScript","React","Angular"]):
        jobs.append("Web Developer")

    if any(s in skills for s in ["Node.js","MongoDB","SQL"]):
        jobs.append("Backend Developer")

    if any(s in skills for s in ["Machine Learning","Data Analysis","Pandas"]):
        jobs.append("Data Analyst")

    if any(s in skills for s in ["AWS","Docker","Linux"]):
        jobs.append("DevOps Engineer")

    # CONTENT
    if any(s in skills for s in ["Content Writing","Blog Writing","Copywriting"]):
        jobs.append("Content Writer")

    if "SEO" in skills:
        jobs.append("SEO Specialist")

    if "Research" in skills:
        jobs.append("Research Analyst")

    if not jobs:
        jobs.append("General Professional Role")

    # -------- SUGGESTIONS --------
    suggestions = []

    if len(skills) < 3:
        suggestions.append("Add more skills")

    if "project" not in text:
        suggestions.append("Add Projects section")

    if "experience" not in text:
        suggestions.append("Add Experience section")

    # -------- SAVE --------
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

    return render_template("result.html",
                           score=score,
                           skills=skills,
                           suggestions=suggestions,
                           jobs=jobs)

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM user_data")
    data = c.fetchall()
    conn.close()

    return render_template("admin.html", data=data)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)