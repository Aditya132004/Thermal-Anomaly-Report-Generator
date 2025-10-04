import os
import sqlite3
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "anomalies.db")

thermal_dir = os.path.join(BASE_DIR, "images", "thermal")
rgb_dir = os.path.join(BASE_DIR, "images", "rgb")

thermal_files = [f for f in os.listdir(thermal_dir) if f.lower().endswith((".jpg", ".png"))]
rgb_files = [f for f in os.listdir(rgb_dir) if f.lower().endswith((".jpg", ".png"))]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    priority TEXT,
    size TEXT,
    loss TEXT,
    temperature REAL,
    parameters TEXT,
    remedial_action TEXT,
    comment TEXT,
    latitude REAL,
    longitude REAL,
    thermal_image TEXT,
    rgb_image TEXT
);
""")

# Clear old data (avoid duplicate pages)
cursor.execute("DELETE FROM anomalies")

categories = ["Loose Connection", "Overheating Transformer", "Damaged Conductor", "Corroded Joint"]
priorities = ["Low", "Medium", "High", "Critical"]
sizes = ["Small", "Medium", "Large"]

# Insert exactly 4 anomalies
for i in range(4):
    category = random.choice(categories)
    priority = random.choice(priorities)
    size = random.choice(sizes)
    temperature = round(random.uniform(40, 120), 2)
    loss = f"{round(random.uniform(1, 50), 2)} kW"
    latitude = round(random.uniform(12.0, 28.0), 6)
    longitude = round(random.uniform(72.0, 88.0), 6)
    parameters = f"Voltage: {random.randint(200, 440)}V, Current: {random.randint(5, 50)}A"
    remedial_action = "Auto-generated action"
    comment = "Auto-detected anomaly"

    # pick random thermal and RGB file
    thermal_file = random.choice(thermal_files)
    rgb_file = random.choice(rgb_files)

    thermal_img = os.path.join("images", "thermal", thermal_file)
    rgb_img = os.path.join("images", "rgb", rgb_file)

    cursor.execute("""
    INSERT INTO anomalies 
    (category, priority, size, loss, temperature, parameters, remedial_action, comment, latitude, longitude, thermal_image, rgb_image)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (category, priority, size, loss, temperature, parameters, remedial_action, comment, latitude, longitude, thermal_img, rgb_img))

conn.commit()
conn.close()
print("Inserted 4 random anomalies into DB using DJI image names")
