from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import calendar
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ashim_todo_2024"

def get_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    now = datetime.today()
    year = int(request.args.get("year", now.year))
    month = int(request.args.get("month", now.month))

    
    if month > 12:
        month = 1
        year += 1
    if month < 1:
        month = 12
        year -= 1

    month_name = datetime(year, month, 1).strftime("%B %Y")
    today_day = now.day if (year == now.year and month == now.month) else -1
    cal = calendar.monthcalendar(year, month)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date FROM todos WHERE user_id = ? AND date LIKE ?",
        (session["user_id"], f"{year}-{month:02d}-%")
    )
    rows = cursor.fetchall()
    conn.close()

    dates_with_todos = set(row["date"] for row in rows)

    return render_template("index.html",
                           cal=cal,
                           year=year,
                           month=month,
                           month_name=month_name,
                           today_day=today_day,
                           dates_with_todos=dates_with_todos)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid username or password!")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            conn.close()
            return render_template("register.html", error="Username already exists!")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/day/<date>")
def day(date):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos WHERE user_id = ? AND date = ?", (session["user_id"], date))
    todos = cursor.fetchall()
    conn.close()

    return render_template("day.html", date=date, todos=todos)

@app.route("/add/<date>", methods=["POST"])
def add(date):
    if "user_id" not in session:
        return redirect(url_for("login"))

    task = request.form["task"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO todos (user_id, date, task) VALUES (?, ?, ?)",
                   (session["user_id"], date, task))
    conn.commit()
    conn.close()
    return redirect(url_for("day", date=date))

@app.route("/done/<int:id>/<date>")
def done(id, date):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?", (id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("day", date=date))

@app.route("/delete/<int:id>/<date>")
def delete(id, date):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("day", date=date))

if __name__ == "__main__":
    app.run(debug=True)