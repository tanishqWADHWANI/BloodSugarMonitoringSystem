"""Show all database tables and their structure"""
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Get all tables
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

print("=" * 80)
print("DATABASE TABLES IN 'blood_sugar_db'")
print("=" * 80)

for table_dict in tables:
    table_name = list(table_dict.values())[0]
    print(f"\n📊 TABLE: {table_name}")
    print("-" * 80)
    
    # Get table structure (use backticks for names with spaces)
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = cursor.fetchall()
    
    print(f"{'Column Name':<30} {'Type':<25} {'Null':<6} {'Key':<6} {'Default':<15}")
    print("-" * 80)
    
    for col in columns:
        print(f"{col['Field']:<30} {col['Type']:<25} {col['Null']:<6} {col['Key']:<6} {str(col['Default']):<15}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
    count = cursor.fetchone()['count']
    print(f"\n📈 Total Rows: {count}")

cursor.close()
conn.close()
