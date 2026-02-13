from flask import Blueprint, render_template, redirect, url_for, session, request
from database import get_connection
import hashlib

manageuser_bp = Blueprint("manageuser", __name__)

# ---------------- MANAGE USERS ----------------
@manageuser_bp.route("/manage_users")
def manage_users():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "Access Denied ❌"

    search = request.args.get("search", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            u.id,
            u.username,
            u.role,

            (SELECT COUNT(*) FROM energy_data WHERE entered_by = u.id) AS energy_count,
            (SELECT COUNT(*) FROM water_data WHERE entered_by = u.id) AS water_count,
            (SELECT COUNT(*) FROM waste_data WHERE entered_by = u.id) AS waste_count,
            (SELECT COUNT(*) FROM greenery_data WHERE entered_by = u.id) AS greenery_count,
            (SELECT COUNT(*) FROM activity_logs WHERE user_id = u.id) AS activity_count

        FROM users u
    """

    if search:
        query += " WHERE u.username LIKE ?"
        cursor.execute(query, (f"%{search}%",))
    else:
        cursor.execute(query)

    users = cursor.fetchall()
    conn.close()

    return render_template("manage_users.html", users=users, search=search)


# ---------------- DELETE USER ----------------
@manageuser_bp.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if session.get("role") != "admin":
        return "Access Denied ❌"

    if user_id == session.get("user_id"):
        return "You cannot delete yourself ❌"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("manageuser.manage_users"))


# ---------------- RESET PASSWORD ----------------
@manageuser_bp.route("/reset_password/<int:user_id>")
def reset_password(user_id):
    if session.get("role") != "admin":
        return "Access Denied ❌"

    new_password = "password123"
    hashed = hashlib.sha256(new_password.encode()).hexdigest()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash=? WHERE id=?",
        (hashed, user_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("manageuser.manage_users"))
