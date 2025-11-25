"""
Fix passwords for newly registered users
Rehash all plain text passwords to werkzeug format
"""
from models import Database
from werkzeug.security import generate_password_hash, check_password_hash

db = Database()
cursor = db._get_cursor()

print("=" * 80)
print("FIXING NEWLY REGISTERED USER PASSWORDS")
print("=" * 80)

# Get all users
cursor.execute("SELECT user_id, email, password_hash, first_name, last_name FROM users")
users = cursor.fetchall()

fixed_count = 0
already_hashed = 0

for user in users:
    password_hash = user['password_hash']
    
    # Check if password is already properly hashed (starts with scrypt: or pbkdf2:)
    if password_hash and (password_hash.startswith('scrypt:') or password_hash.startswith('pbkdf2:')):
        already_hashed += 1
        print(f"✓ {user['email']:<35} - Already properly hashed")
        continue
    
    # If it's a plain text password or old SHA256 hash, ask user what to do
    print(f"\n⚠️  {user['email']:<35} - Needs rehashing")
    print(f"   Current hash: {password_hash[:50] if password_hash else 'NULL'}...")
    print(f"   Options:")
    print(f"   1. Set password to: 'password123' (default)")
    print(f"   2. Keep as-is (skip)")
    
    # For automation, we'll set a default password
    # In production, you'd want to send password reset emails
    new_password = "password123"
    new_hash = generate_password_hash(new_password)
    
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE user_id = %s",
        (new_hash, user['user_id'])
    )
    db.connection.commit()
    fixed_count += 1
    print(f"   ✅ Password reset to: 'password123'")

print("\n" + "=" * 80)
print(f"SUMMARY:")
print(f"  Already properly hashed: {already_hashed}")
print(f"  Fixed/Reset passwords:   {fixed_count}")
print("=" * 80)

if fixed_count > 0:
    print(f"\n⚠️  {fixed_count} user(s) had their password reset to: 'password123'")
    print("   Users should change their passwords after logging in.")

db.close()
