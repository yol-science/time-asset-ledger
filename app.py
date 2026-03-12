from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "tim.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        hourly_rate INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        minutes INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "save_rate":
            hourly_rate = int(request.form["hourly_rate"])
            cursor.execute("""
            INSERT INTO settings (id, hourly_rate)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET hourly_rate = excluded.hourly_rate
            """, (hourly_rate,))

        elif action == "add_log":
            minutes = int(request.form["minutes"])
            cursor.execute("""
            INSERT INTO logs (minutes, created_at)
            VALUES (?, ?)
            """, (minutes, datetime.now().strftime("%Y-%m-%d %H:%M")))

        elif action == "delete_log":
            log_id = int(request.form["log_id"])
            cursor.execute("DELETE FROM logs WHERE id = ?", (log_id,))

        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    cursor.execute("SELECT hourly_rate FROM settings WHERE id = 1")
    setting = cursor.fetchone()
    hourly_rate = setting["hourly_rate"] if setting else 0

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_month = now.strftime("%Y-%m")
    current_year = now.strftime("%Y")

    cursor.execute("""
    SELECT SUM(minutes) AS today_minutes
    FROM logs
    WHERE strftime('%Y-%m-%d', created_at) = ?
    """, (today,))
    today_result = cursor.fetchone()
    today_minutes = today_result["today_minutes"] if today_result["today_minutes"] else 0


    cursor.execute("""
    SELECT SUM(minutes) AS month_minutes
    FROM logs
    WHERE strftime('%Y-%m', created_at) = ?
    """, (current_month,))
    month_result = cursor.fetchone()
    month_minutes = month_result["month_minutes"] if month_result["month_minutes"] else 0

    cursor.execute("""
    SELECT SUM(minutes) AS year_minutes
    FROM logs
    WHERE strftime('%Y', created_at) = ?
    """, (current_year,))
    year_result = cursor.fetchone()
    year_minutes = year_result["year_minutes"] if year_result["year_minutes"] else 0

    cursor.execute("""
    SELECT
        id,
        minutes,
        strftime('%Y-%m-%d %H:%M', created_at) as created_at
    FROM logs
    ORDER BY created_at DESC
    """)
    logs = cursor.fetchall()

    today_loss = int(hourly_rate * today_minutes / 60)
    monthly_loss = int(hourly_rate * month_minutes / 60)
    yearly_loss = int(hourly_rate * year_minutes / 60)

    conn.close()

    return render_template(
        "index.html",
        hourly_rate=hourly_rate,
        month_minutes=month_minutes,
        year_minutes=year_minutes,
        monthly_loss=monthly_loss,
        yearly_loss=yearly_loss,
        logs=logs,
        today_minutes=today_minutes,
        today_loss=today_loss
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)