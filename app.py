from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"


def get_db():
    return sqlite3.connect("database.db", timeout=10)


# ---------- DATABASE ----------
with get_db() as con:
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )
    """)
    con.commit()


# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()

        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()

        con.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            return "Invalid username or password"

    return render_template("login.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        con = get_db()
        cur = con.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, password)
            )
            con.commit()

        except:
            return "User already exists"

        finally:
            con.close()

        return redirect("/")

    return render_template("register.html")


# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    uid = session["user_id"]
    con = get_db()
    cur = con.cursor()

    # ADD EXPENSE
    if request.method == "POST":
        cur.execute("""
        INSERT INTO expenses(user_id,title,amount,category,date)
        VALUES(?,?,?,?,?)
        """,(
            uid,
            request.form["title"],
            float(request.form["amount"]),
            request.form["category"],
            request.form["date"]
        ))
        con.commit()

    # FETCH DATA
    cur.execute("SELECT * FROM expenses WHERE user_id=?", (uid,))
    data = cur.fetchall()

    con.close()

    total = sum([float(x[3]) for x in data])

    # BAR CHART DATA (date-wise)
    date_data = {}
    for row in data:
        date_data[row[5]] = date_data.get(row[5], 0) + float(row[3])

    bar_labels = list(date_data.keys())
    bar_values = list(date_data.values())

    return render_template("dashboard.html",
                           expenses=data,
                           total=total,
                           bar_labels=bar_labels,
                           bar_values=bar_values)


# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    con = get_db()
    cur = con.cursor()
    cur.execute("DELETE FROM expenses WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)