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
