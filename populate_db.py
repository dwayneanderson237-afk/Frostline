import sqlite3

DATABASE = 'frostline_coons.db'

kittens = [
    ("Luna", "Female", "Silver", "Playful and affectionate kitten.", "luna.jpg", "Available", 1200),
    ("Leo", "Male", "Brown Tabby", "Curious and smart little guy.", "leo.jpg", "Available", 1300),
    ("Milo", "Male", "Black", "Gentle and friendly kitten.", "milo.jpg", "Available", 1250),
    ("Bella", "Female", "Golden", "Loves to cuddle and play.", "bella.jpg", "Available", 1400),
    ("Shadow", "Male", "Gray", "Calm and intelligent kitten.", "shadow.jpg", "Available", 1350),
    ("Daisy", "Female", "Cream", "Playful and energetic.", "daisy.jpg", "Available", 1200),
    ("Oliver", "Male", "Orange", "Affectionate and social.", "oliver.jpg", "Available", 1300),
    ("Chloe", "Female", "Silver Tabby", "Sweet and friendly kitten.", "chloe.jpg", "Available", 1400),
    ("Simba", "Male", "Brown", "Curious and playful.", "simba.jpg", "Available", 1250),
    ("Lily", "Female", "White", "Gentle and loving.", "lily.jpg", "Available", 1300)
]

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

for k in kittens:
    cursor.execute("""
        INSERT INTO kittens (name, gender, color, description, images, availability, price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, k)

conn.commit()
conn.close()

print("✅ Sample kittens added successfully!")
