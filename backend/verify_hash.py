import sys
from models import Database

print("=== CHECKING PASSWORD HASHES ===", flush=True)
sys.stdout.flush()

db = Database()
admin = db.get_user(999)
staff = db.get_user(106)

if admin:
    admin_hash = admin['password_hash']
    print(f"\nAdmin hash length: {len(admin_hash)}", flush=True)
    print(f"Admin hash first 50 chars: {admin_hash[:50]}", flush=True)
    print(f"Is SHA256 (64 chars hex)?: {len(admin_hash) == 64 and all(c in '0123456789abcdef' for c in admin_hash)}", flush=True)
    print(f"Is werkzeug (starts pbkdf2)?: {admin_hash.startswith('pbkdf2')}", flush=True)
else:
    print("Admin not found!", flush=True)

if staff:
    staff_hash = staff['password_hash']
    print(f"\nStaff hash length: {len(staff_hash)}", flush=True)
    print(f"Staff hash first 50 chars: {staff_hash[:50]}", flush=True)
    print(f"Is SHA256 (64 chars hex)?: {len(staff_hash) == 64 and all(c in '0123456789abcdef' for c in staff_hash)}", flush=True)
    print(f"Is werkzeug (starts pbkdf2)?: {staff_hash.startswith('pbkdf2')}", flush=True)
else:
    print("Staff not found!", flush=True)

sys.stdout.flush()
