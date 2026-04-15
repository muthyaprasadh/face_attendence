import cv2
import os
import numpy as np
import sqlite3
from datetime import datetime

DATASET_PATH = "known_faces"
CASCADE_PATH = "haarcascade_frontalface_default.xml"

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
labels = []
label_map = {}

current_label = 0

# =========================
# LOAD DATASET (FIXED)
# =========================
for person in sorted(os.listdir(DATASET_PATH)):  # ✅ FIX 1: SORT
    person_path = os.path.join(DATASET_PATH, person)

    if not os.path.isdir(person_path):
        continue

    label_map[current_label] = person

    for img_name in sorted(os.listdir(person_path)):  # ✅ FIX 2: SORT IMAGES
        img_path = os.path.join(person_path, img_name)

        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        img = cv2.resize(img, (200, 200))
        faces.append(img)
        labels.append(current_label)

    current_label += 1

# Debug (optional)
print("Label Map:", label_map)

# Train model
recognizer.train(faces, np.array(labels))


# =========================
# MARK ATTENDANCE
# =========================
def mark_attendance(name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT
        )
    """)

    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")

    # Prevent duplicate entry same day
    cursor.execute("SELECT * FROM attendance WHERE name=? AND date=?", (name, date))

    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO attendance VALUES (NULL, ?, ?, ?)",
                       (name, date, time))
        conn.commit()

    conn.close()


# =========================
# CAMERA STREAM
# =========================
def generate_frames():
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces_detected:
            face_img = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_img, (200, 200))

            label, confidence = recognizer.predict(face_resized)

            # ✅ FIX 3: STRICT CONFIDENCE
            if confidence < 60:
                name = label_map[label]
                color = (0, 255, 0)
                mark_attendance(name)
            else:
                name = "Unknown"
                color = (0, 0, 255)

            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

            # ✅ Show name + confidence
            cv2.putText(frame, f"{name} ({int(confidence)})",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9, color, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')