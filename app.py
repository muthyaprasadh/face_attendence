from flask import Flask, render_template, Response
from camera import generate_frames
import sqlite3

app = Flask(__name__)

# 🔥 ADD THIS FUNCTION
def clear_attendance():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance")
    conn.commit()
    conn.close()

# 🔥 CALL IT HERE (runs when app starts)
clear_attendance()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video")
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/admin")
def admin():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance")
    records = cursor.fetchall()
    conn.close()
    return render_template("admin.html", records=records)

if __name__ == "__main__":
    app.run(debug=True)