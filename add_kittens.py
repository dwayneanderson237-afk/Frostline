import sqlite3

# Connect to the database
conn = sqlite3.connect('frostline_coons.db')
cursor = conn.cursor()

# Ensure table exists with price column
cursor.execute('''
CREATE TABLE IF NOT EXISTS kittens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    gender TEXT,
    color TEXT,
    description TEXT,
    images TEXT,
    availability TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    price REAL DEFAULT 0
)
''')

# Kittens to add
kittens = [
    ("Fluffy", "Male", "Brown Tabby", "Playful and gentle.", "fluffy.jpg", "Available", 900),
    ("Luna", "Female", "Silver", "Sweet and fluffy.", "luna.jpg", "Available", 1200),
    ("Leo", "Male", "Black", "Friendly and affectionate.", "leo.jpg", "Available", 1500),
    ("Misty", "Female", "Blue", "Calm and loving.", "misty.jpg", "Available", 900)
]

# Insert kittens
for k in kittens:
    cursor.execute('''
        INSERT INTO kittens (name, gender, color, description, images, availability, price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', k)

# Commit and close
conn.commit()
conn.close()
print("Kittens added successfully!")
