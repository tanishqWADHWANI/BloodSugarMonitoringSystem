from models import Database

db = Database()
cursor = db._get_cursor()

print("Checking specialist_feedback table...")

try:
    # Check if table exists
    cursor.execute("SHOW TABLES LIKE 'specialist_feedback'")
    result = cursor.fetchall()
    
    if len(result) == 0:
        print("❌ Table 'specialist_feedback' does NOT exist!")
        print("\nChecking for similar tables:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[list(table.keys())[0]]
            if 'feedback' in table_name.lower() or 'specialist' in table_name.lower():
                print(f"  - {table_name}")
    else:
        print("✓ Table 'specialist_feedback' exists")
        cursor.execute("DESCRIBE specialist_feedback")
        print("\nTable structure:")
        for row in cursor.fetchall():
            print(f"  {row['Field']:<20} {row['Type']:<20}")
            
        # Check if there's any data
        cursor.execute("SELECT COUNT(*) as count FROM specialist_feedback")
        count = cursor.fetchone()['count']
        print(f"\nTotal feedback records: {count}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    cursor.close()
    db.close()
