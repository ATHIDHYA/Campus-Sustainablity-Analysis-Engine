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

    labels = [r["label"] for r in rows]
    scores = [r["total_score"] for r in rows]

    # ---------- KPI ----------
    def get_avg(table):
        cursor.execute(f"SELECT AVG(value) as avg FROM {table}")
        result = cursor.fetchone()["avg"]
        return round(result, 2) if result else 0

    avg_energy = get_avg("energy_data")
    avg_water = get_avg("water_data")
    avg_waste = get_avg("waste_data")
    avg_greenery = get_avg("greenery_data")

    overall_score = round(sum(scores) / len(scores), 2) if scores else 0

    # ---------- Grade ----------
    if overall_score >= 85:
        grade = "A"
    elif overall_score >= 70:
        grade = "B"
    elif overall_score >= 50:
        grade = "C"
    else:
        grade = "D"

    # ---------- Prediction ----------
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

        next_label = "Next"
        labels_with_prediction.append(next_label)
        scores_with_prediction.append(predicted_score)

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
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
        return redirect(url_for("dashboard"))

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
        return redirect(url_for("dashboard"))

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
        return redirect(url_for("dashboard"))

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
        return redirect(url_for("dashboard"))

    return render_template("greenery_entry.html")


# -------------------- CALCULATE SCORE --------------------
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
        r = cursor.fetchone()["avg"]
        return r if r else 0

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

    return redirect(url_for("dashboard"))


# -------------------- EXCEL UPLOAD --------------------
@app.route("/upload_sustainability_excel", methods=["GET", "POST"])
def upload_sustainability_excel():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["file"]

        if not file or not file.filename.endswith(".xlsx"):
            return "❌ Upload valid .xlsx file"

        df = pd.read_excel(file)

        required_cols = {"month", "year", "energy", "water", "waste", "greenery"}
        if not required_cols.issubset(df.columns):
            return "❌ Invalid Excel format"

        conn = get_connection()
        cursor = conn.cursor()

        for _, row in df.iterrows():
            month = int(row["month"])
            year = int(row["year"])

            energy = float(row["energy"])
            water = float(row["water"])
            waste = float(row["waste"])
            greenery = float(row["greenery"])

            energy_score = max(0, 100 - energy / 10)
            water_score = max(0, 100 - water / 10)
            waste_score = max(0, 100 - waste / 5)
            greenery_score = min(100, greenery / 2)

            total_score = round(
                (energy_score + water_score + waste_score + greenery_score) / 4, 2
            )

            cursor.execute("""
                INSERT OR REPLACE INTO sustainability_scores
                (month, year, energy_score, water_score, waste_score, greenery_score, total_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                month, year,
                energy_score, water_score, waste_score, greenery_score, total_score
            ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("upload_sustainability_excel.html")


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
        return redirect(url_for("dashboard"))

    return render_template("add_user.html")


@app.route("/manage_users")
def manage_users():
    if "user_id" not in session or session["role"] != "admin":
        return "❌ Access denied"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("manage_users.html", users=users)


# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
