import sqlite3
import os

# Path to your database and images folder
DATABASE = 'frostline_coons.db'
IMAGES_FOLDER = 'static/images/'

# Connect to DB
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Get all kittens
cursor.execute("SELECT id, name FROM kittens")
kittens = cursor.fetchall()

# Get list of image files in the folder
image_files = os.listdir(IMAGES_FOLDER)

for kitten in kittens:
    kid = kitten[0]
    name = kitten[1].lower()  # make lowercase for matching

    # Try to find a matching image file
    matched_file = None
    for f in image_files:
        if name in f.lower():  # simple match by kitten name
            matched_file = f
            break

    if matched_file:
        cursor.execute("UPDATE kittens SET images=? WHERE id=?", (matched_file, kid))
        print(f"Updated {name} → {matched_file}")
    else:
        print(f"No image found for {name}, skipping.")

conn.commit()
conn.close()
print("Database images synced with static/images folder!")
