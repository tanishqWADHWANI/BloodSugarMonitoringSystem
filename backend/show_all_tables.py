from models import Database

db = Database()
cursor = db._get_cursor()

print("=" * 80)
print("ALL TABLES IN DATABASE")
print("=" * 80)

cursor.execute('SHOW TABLES')
tables = cursor.fetchall()

for table in tables:
    table_name = table[list(table.keys())[0]]
    print(f"\n{table_name}:")
    cursor.execute(f'DESCRIBE {table_name}')
    for row in cursor.fetchall():
        print(f'  {row["Field"]:<25} {row["Type"]:<20}')

db.close()
