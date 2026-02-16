from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_connection
import pandas as pd

dataentry_bp = Blueprint("dataentry", __name__, url_prefix="/data")


# ================= COMMON INSERT FUNCTION =================
def insert_record(table, value, month, year, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO {table} (value, month, year, entered_by) VALUES (?, ?, ?, ?)",
        (value, month, year, user_id)
    )
    conn.commit()
    conn.close()


# ================= ENERGY =================
@dataentry_bp.route("/energy", methods=["GET", "POST"])
def energy_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_record(
            "energy_data",
            request.form["value"],
            request.form["month"],
            request.form["year"],
            session["user_id"]
        )
        return redirect(url_for("dashboard"))

    return render_template("energy_entry.html")



# ================= WATER =================
@dataentry_bp.route("/water", methods=["GET", "POST"])
def water_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_record(
            "water_data",
            request.form["value"],
            request.form["month"],
            request.form["year"],
            session["user_id"]
        )
        return redirect(url_for("dashboard"))

    return render_template("water_entry.html")


# ================= WASTE =================
@dataentry_bp.route("/waste", methods=["GET", "POST"])
def waste_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_record(
            "waste_data",
            request.form["value"],
            request.form["month"],
            request.form["year"],
            session["user_id"]
        )
        return redirect(url_for("dashboard"))

    return render_template("waste_entry.html")


# ================= GREENERY =================
@dataentry_bp.route("/greenery", methods=["GET", "POST"])
def greenery_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_record(
            "greenery_data",
            request.form["value"],
            request.form["month"],
            request.form["year"],
            session["user_id"]
        )
        return redirect(url_for("dashboard"))

    return render_template("greenery_entry.html")

ALLOWED_TABLES = {
    "energy_data",
    "water_data",
    "waste_data",
    "greenery_data"
}

def recalculate_month_score(month, year):
    conn = get_connection()
    cursor = conn.cursor()

    def get_avg(table):
        cursor.execute("""
            SELECT AVG(value) as avg
            FROM {}
            WHERE month=? AND year=?
        """.format(table), (month, year))
        result = cursor.fetchone()["avg"]
        return result if result else 0

    energy = get_avg("energy_data")
    water = get_avg("water_data")
    waste = get_avg("waste_data")
    greenery = get_avg("greenery_data")

    # Score logic (same as upload)
    energy_score = max(0, 100 - energy / 10)
    water_score = max(0, 100 - water / 10)
    waste_score = max(0, 100 - waste / 5)
    greenery_score = min(100, greenery / 2)

    total = round(
        (energy_score + water_score +
         waste_score + greenery_score) / 4, 2
    )

    # Remove old score
    cursor.execute("""
        DELETE FROM sustainability_scores
        WHERE month=? AND year=?
    """, (month, year))

    # Insert new score
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

# 
# ---------------- VIEW ENTRIES ----------------
@dataentry_bp.route("/view_entries")
def view_entries():
    if "user_id" not in session:
        return redirect(url_for("login"))

    table = request.args.get("type", "energy_data")
    month = request.args.get("month")
    year = request.args.get("year")

    if table not in ALLOWED_TABLES:
        table = "energy_data"

    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT t.id, t.value, t.month, t.year, u.username
        FROM {table} t
        JOIN users u ON t.entered_by = u.id
        WHERE 1=1
    """

    params = []

    if month:
        query += " AND t.month=?"
        params.append(month)

    if year:
        query += " AND t.year=?"
        params.append(year)

    query += " ORDER BY t.year DESC, t.month DESC"

    cursor.execute(query, params)
    entries = cursor.fetchall()

    conn.close()

    return render_template(
        "view_entries.html",
        entries=entries,
        selected_table=table,
        selected_month=month,
        selected_year=year
    )


@dataentry_bp.route("/delete_entry/<table>/<int:id>")
def delete_entry(table, id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if table not in ALLOWED_TABLES:
        return "Invalid table ❌"

    conn = get_connection()
    cursor = conn.cursor()

    # Get month & year before deleting
    cursor.execute(f"SELECT month, year FROM {table} WHERE id=?", (id,))
    row = cursor.fetchone()

    if row:
        month = row["month"]
        year = row["year"]

        cursor.execute(f"DELETE FROM {table} WHERE id=?", (id,))
        conn.commit()

        # Recalculate after delete
        recalculate_month_score(month, year)

    conn.close()

    return redirect(url_for("dataentry.view_entries", type=table))

@dataentry_bp.route("/edit_entry/<table>/<int:id>", methods=["GET", "POST"])
def edit_entry(table, id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if table not in ALLOWED_TABLES:
        return "Invalid table ❌"

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        value = request.form["value"]
        month = request.form["month"]
        year = request.form["year"]

        cursor.execute(f"""
            UPDATE {table}
            SET value=?, month=?, year=?
            WHERE id=?
        """, (value, month, year, id))

        conn.commit()

        # Recalculate after edit
        recalculate_month_score(month, year)

        conn.close()

        return redirect(url_for("dataentry.view_entries", type=table))

    cursor.execute(f"SELECT * FROM {table} WHERE id=?", (id,))
    entry = cursor.fetchone()
    conn.close()

    return render_template(
        "edit_entry.html",
        entry=entry,
        table=table
    )
