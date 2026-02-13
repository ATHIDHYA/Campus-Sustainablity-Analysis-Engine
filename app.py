from manageuser import manageuser_bp
from dataentry import dataentry_bp
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, send_file
)
import numpy as np
from database import get_connection
import hashlib
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import json
import os

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")
app.register_blueprint(manageuser_bp)
app.register_blueprint(dataentry_bp)


ALLOWED_TABLES = {
    "energy_data",
    "water_data",
    "waste_data",
    "greenery_data"
}

# -------------------- HELPERS --------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def log_activity(action):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activity_logs (user_id, action) VALUES (?, ?)",
        (session["user_id"], action)
    )
    conn.commit()
    conn.close()


def insert_data(table, value, month, year):
    if table not in ALLOWED_TABLES:
        raise ValueError("Invalid table")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO {table} (value, month, year, entered_by) VALUES (?, ?, ?, ?)",
        (value, month, year, session["user_id"])
    )
    conn.commit()
    conn.close()

    log_activity(f"Inserted into {table}")


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
            log_activity("Logged in")
            return redirect(url_for("dashboard"))

        return "Invalid login ❌"

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

    labels = [r["label"] for r in rows]
    scores = [r["total_score"] for r in rows]

    def get_avg(table):
        cursor.execute(f"SELECT AVG(value) as avg FROM {table}")
        r = cursor.fetchone()["avg"]
        return round(r, 2) if r else 0

    avg_energy = get_avg("energy_data")
    avg_water = get_avg("water_data")
    avg_waste = get_avg("waste_data")
    avg_greenery = get_avg("greenery_data")

    overall_score = round(sum(scores) / len(scores), 2) if scores else 0

    grade = "D"
    if overall_score >= 85:
        grade = "A"
    elif overall_score >= 70:
        grade = "B"
    elif overall_score >= 50:
        grade = "C"

    predicted_score = None
    trend = "Stable"

    labels_with_prediction = labels.copy()
    scores_with_prediction = scores.copy()

    if len(scores) >= 2:
        x = np.arange(len(scores))
        y = np.array(scores)
        m, b = np.polyfit(x, y, 1)
        predicted_score = round(m * len(scores) + b, 2)

        if predicted_score > scores[-1]:
            trend = "Improving 📈"
        elif predicted_score < scores[-1]:
            trend = "Declining 📉"

        labels_with_prediction.append("Next")
        scores_with_prediction.append(predicted_score)

    conn.close()

    return render_template(
        "dashboard.html",
        role=session["role"],
        labels=json.dumps(labels_with_prediction),
        scores=json.dumps(scores_with_prediction),
        avg_energy=avg_energy,
        avg_water=avg_water,
        avg_waste=avg_waste,
        avg_greenery=avg_greenery,
        overall_score=overall_score,
        grade=grade,
        predicted_score=predicted_score,
        trend=trend
    )

# -------------------- EXCEL UPLOAD --------------------
@app.route("/upload_sustainability_excel", methods=["GET", "POST"])
def upload_sustainability_excel():
    if "user_id" not in session:
        return redirect(url_for("login"))

    avg_uploaded = None

    if request.method == "POST":
        file = request.files["file"]

        if file and file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)

            conn = get_connection()
            cursor = conn.cursor()

            total_scores = []

            for _, row in df.iterrows():
                month = int(row["month"])
                year = int(row["year"])
                energy = float(row["energy"])
                water = float(row["water"])
                waste = float(row["waste"])
                greenery = float(row["greenery"])

                # INSERT RAW DATA (NO extra connection)
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

                # CALCULATE SCORE
                energy_score = max(0, 100 - energy / 10)
                water_score = max(0, 100 - water / 10)
                waste_score = max(0, 100 - waste / 5)
                greenery_score = min(100, greenery / 2)

                total = round(
                    (energy_score + water_score +
                     waste_score + greenery_score) / 4, 2
                )

                total_scores.append(total)

                # Remove old score if exists
                cursor.execute(
                    "DELETE FROM sustainability_scores WHERE month=? AND year=?",
                    (month, year)
                )

                cursor.execute("""
                    INSERT INTO sustainability_scores
                    (month, year, energy_score, water_score,
                     waste_score, greenery_score, total_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (month, year,
                      energy_score, water_score,
                      waste_score, greenery_score, total))

            conn.commit()
            conn.close()

            avg_uploaded = round(sum(total_scores) / len(total_scores), 2)

    return render_template(
        "upload_sustainability_excel.html",
        avg_uploaded=avg_uploaded
    )

# -------------------- PDF EXPORT --------------------

@app.route("/export_pdf")
def export_pdf():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT month, year, total_score
        FROM sustainability_scores
        ORDER BY year, month
    """)
    rows = cursor.fetchall()
    conn.close()

    file_path = "report.pdf"
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica", 12)
    c.drawString(50, y, "Sustainability Report")
    y -= 30

    for r in rows:
        c.drawString(
            50, y,
            f"Month: {r['month']}  Year: {r['year']}  Score: {r['total_score']}"
        )
        y -= 20

    c.save()

    return send_file(file_path, as_attachment=True)


# -------------------- ADMIN --------------------

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "Access Denied ❌"

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        print("FORM DATA:", request.form)

        print("DEBUG:", username, password, role)

        if not username or not password or not role:
            error = "All fields are required ❌"
            return render_template("add_user.html", error=error)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            conn.close()
            error = "Username already exists ❌"
            return render_template("add_user.html", error=error)

        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, (username, hash_password(password), role))

        conn.commit()
        conn.close()

        return redirect(url_for("add_user"))

    return render_template("add_user.html", error=error)


# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run(debug=True)
