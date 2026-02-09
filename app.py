from flask import (
    Flask, render_template, request,
    redirect, url_for, session, send_file
)
from database import get_connection
import hashlib
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"


# -------------------- HELPERS --------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# -------------------- AUTH --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        return "❌ Invalid login"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT month || '-' || year AS label, total_score
        FROM sustainability_scores
        ORDER BY year, month
    """)
    rows = cursor.fetchall()
    conn.close()

    labels = [r["label"] for r in rows]
    scores = [r["total_score"] for r in rows]

    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        labels=labels,
        scores=scores
    )


# -------------------- DATA ENTRY --------------------
def insert_data(table, value, month, year):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO {table} (value, month, year, entered_by) VALUES (?, ?, ?, ?)",
        (value, month, year, session["user_id"])
    )
    conn.commit()
    conn.close()


@app.route("/energy", methods=["GET", "POST"])
def energy_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_data("energy_data",
                    request.form["value"],
                    request.form["month"],
                    request.form["year"])
        return "✅ Energy data saved"

    return render_template("energy_entry.html")


@app.route("/water", methods=["GET", "POST"])
def water_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_data("water_data",
                    request.form["value"],
                    request.form["month"],
                    request.form["year"])
        return "✅ Water data saved"

    return render_template("water_entry.html")


@app.route("/waste", methods=["GET", "POST"])
def waste_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_data("waste_data",
                    request.form["value"],
                    request.form["month"],
                    request.form["year"])
        return "✅ Waste data saved"

    return render_template("waste_entry.html")


@app.route("/greenery", methods=["GET", "POST"])
def greenery_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_data("greenery_data",
                    request.form["value"],
                    request.form["month"],
                    request.form["year"])
        return "✅ Greenery data saved"

    return render_template("greenery_entry.html")


# -------------------- SCORE CALCULATION --------------------
@app.route("/calculate_score/<int:month>/<int:year>")
def calculate_score(month, year):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    def avg(table):
        cursor.execute(
            f"SELECT AVG(value) as avg FROM {table} WHERE month=? AND year=?",
            (month, year)
        )
        r = cursor.fetchone()
        return r["avg"] if r["avg"] else 0

    energy = avg("energy_data")
    water = avg("water_data")
    waste = avg("waste_data")
    greenery = avg("greenery_data")

    energy_score = max(0, 100 - energy / 10)
    water_score = max(0, 100 - water / 10)
    waste_score = max(0, 100 - waste / 5)
    greenery_score = min(100, greenery / 2)

    total = round(
        (energy_score + water_score + waste_score + greenery_score) / 4, 2
    )

    cursor.execute(
        "DELETE FROM sustainability_scores WHERE month=? AND year=?",
        (month, year)
    )

    cursor.execute("""
        INSERT INTO sustainability_scores
        (month, year, energy_score, water_score, waste_score, greenery_score, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (month, year,
          energy_score, water_score, waste_score, greenery_score, total))

    conn.commit()
    conn.close()

    return f"<h3>Total Sustainability Score: {total}</h3><a href='/dashboard'>Back</a>"


# -------------------- EXCEL UPLOAD --------------------
@app.route("/upload_sustainability_excel", methods=["GET", "POST"])
def upload_sustainability_excel():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["file"]

        if not file or not file.filename.endswith(".xlsx"):
            return "❌ Please upload a valid Excel (.xlsx) file"

        df = pd.read_excel(file)

        required_cols = {"month", "year", "energy", "water", "waste", "greenery"}
        if not required_cols.issubset(df.columns):
            return "❌ Excel must contain month, year, energy, water, waste, greenery"

        conn = get_connection()
        cursor = conn.cursor()

        for _, row in df.iterrows():
            month = int(row["month"])
            year = int(row["year"])

            # ✅ Prevent duplicate score entry
            cursor.execute("""
                SELECT 1 FROM sustainability_scores
                WHERE month=? AND year=?
            """, (month, year))

            if cursor.fetchone():
                continue  # skip already calculated month/year

            energy = float(row["energy"])
            water = float(row["water"])
            waste = float(row["waste"])
            greenery = float(row["greenery"])

            # ---- Insert raw data ----
            cursor.execute(
                "INSERT INTO energy_data (value, month, year, entered_by) VALUES (?, ?, ?, ?)",
                (energy, month, year, session["user_id"])
            )
            cursor.execute(
                "INSERT INTO water_data (value, month, year, entered_by) VALUES (?, ?, ?, ?)",
                (water, month, year, session["user_id"])
            )
            cursor.execute(
                "INSERT INTO waste_data (value, month, year, entered_by) VALUES (?, ?, ?, ?)",
                (waste, month, year, session["user_id"])
            )
            cursor.execute(
                "INSERT INTO greenery_data (value, month, year, entered_by) VALUES (?, ?, ?, ?)",
                (greenery, month, year, session["user_id"])
            )

            # ---- Auto-calculate scores ----
            energy_score = max(0, 100 - energy / 10)
            water_score = max(0, 100 - water / 10)
            waste_score = max(0, 100 - waste / 5)
            greenery_score = min(100, greenery / 2)

            total_score = round(
                (energy_score + water_score + waste_score + greenery_score) / 4, 2
            )

            cursor.execute("""
                INSERT INTO sustainability_scores
                (month, year, energy_score, water_score, waste_score, greenery_score, total_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                month, year,
                energy_score, water_score, waste_score, greenery_score, total_score
            ))

        conn.commit()
        conn.close()

        return "✅ Excel uploaded, duplicates skipped & scores calculated!"

    return render_template("upload_sustainability_excel.html")


# -------------------- PDF REPORT --------------------
@app.route("/report/<int:year>")
def generate_report(year):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT month, total_score
        FROM sustainability_scores
        WHERE year=?
        ORDER BY month
    """, (year,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "❌ No data available"

    filename = f"sustainability_report_{year}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    y = 800

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Campus Sustainability Report")
    y -= 40

    c.setFont("Helvetica", 10)
    for r in rows:
        c.drawString(50, y, f"Month {r['month']} → Score: {r['total_score']}")
        y -= 20

    c.save()
    return send_file(filename, as_attachment=True)


# -------------------- ADMIN --------------------
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "user_id" not in session or session["role"] != "admin":
        return "❌ Access denied"

    if request.method == "POST":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (
                request.form["username"],
                hash_password(request.form["password"]),
                request.form["role"]
            )
        )
        conn.commit()
        conn.close()
        return "✅ User added"

    return render_template("add_user.html")

@app.route("/download_excel_template")
def download_excel_template():
    import pandas as pd

    df = pd.DataFrame({
        "month": [1],
        "year": [2025],
        "energy": [1200],
        "water": [800],
        "waste": [300],
        "greenery": [150]
    })

    file_name = "sustainability_template.xlsx"
    df.to_excel(file_name, index=False)

    return send_file(file_name, as_attachment=True)

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
