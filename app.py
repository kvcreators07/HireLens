from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import PyPDF2

app = Flask(__name__)
app.secret_key = "secret123"

# 📁 Upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🗄️ DB INIT
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # User data table
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

# 🏠 Home
@app.route("/")
def index():
    return render_template("index.html")

# 🔐 Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# 🔐 Login
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

# 🚪 Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# 📊 Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# 🧠 ANALYZE (MAIN)
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

    # 📄 Read PDF
    if file.filename.endswith(".pdf"):
        pdf = PyPDF2.PdfReader(filepath)
        for page in pdf.pages:
            text += page.extract_text()

    text = text.lower()

    # 🧠 Skills
    skills = []
    if "python" in text:
        skills.append("Python")
    if "html" in text:
        skills.append("HTML")
    if "css" in text:
        skills.append("CSS")
    if "javascript" in text:
        skills.append("JavaScript")

    # 🎯 Score
    score = len(skills) * 20

    # 💼 Jobs
    jobs = []
    if "python" in skills:
        jobs.append("Python Developer")
    if "html" in skills or "css" in skills:
        jobs.append("Web Developer")
    if "javascript" in skills:
        jobs.append("Frontend Developer")

    # 💡 Suggestions
    suggestions = []
    if "projects" not in text:
        suggestions.append("Add Projects section")

    # 💾 SAVE TO DB
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

# 📊 ADMIN TABLE
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