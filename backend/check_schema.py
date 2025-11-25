from models import Database

db = Database()
cursor = db._get_cursor()

print("=" * 80)
print("DATABASE SCHEMA CHECK")
print("=" * 80)

# Check specialists table
cursor.execute('DESCRIBE specialists')
print('\nSPECIALISTS TABLE:')
for row in cursor.fetchall():
    print(f'  {row["Field"]:<25} {row["Type"]:<20}')

# Check staff table
cursor.execute('DESCRIBE staff')
print('\nSTAFF TABLE:')
for row in cursor.fetchall():
    print(f'  {row["Field"]:<25} {row["Type"]:<20}')

# Check blood_sugar_readings table
cursor.execute('DESCRIBE blood_sugar_readings')
print('\nBLOOD_SUGAR_READINGS TABLE:')
for row in cursor.fetchall():
    print(f'  {row["Field"]:<25} {row["Type"]:<20}')

print("\n" + "=" * 80)

db.close()
