from models import Database

db = Database()
cursor = db._get_cursor()

print("=" * 80)
print("ALL USERS IN DATABASE")
print("=" * 80)

cursor.execute("""
    SELECT user_id, email, first_name, last_name, role 
    FROM users 
    ORDER BY role, user_id
""")

current_role = None
for row in cursor.fetchall():
    role = row['role'].upper()
    if role != current_role:
        print(f"\n{role}S:")
        current_role = role
    print(f"  [{row['user_id']:3d}] {row['email']:<30} | {row['first_name']} {row['last_name']}")

db.close()
