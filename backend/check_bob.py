import mysql.connector

# Direct connection
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

# Find Bob
cursor1 = conn.cursor(dictionary=True)
cursor1.execute("SELECT user_id, email, first_name FROM users WHERE email LIKE 'bob%'")
results = cursor1.fetchall()
bob = results[0] if results else None
cursor1.close()
print(f"Bob's record: {bob}")

if bob:
    user_id = bob['user_id']
    
    # Check health records count
    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute(f"SELECT COUNT(*) as count FROM bloodsugarreadings WHERE user_id = {user_id}")
    count_results = cursor2.fetchall()
    count = count_results[0] if count_results else {'count': 0}
    cursor2.close()
    print(f"Bob's health records count: {count['count']}")
    
    # Get records
    cursor3 = conn.cursor(dictionary=True)
    cursor3.execute(f"SELECT reading_id, value, date_time, status FROM bloodsugarreadings WHERE user_id = {user_id} ORDER BY date_time DESC LIMIT 10")
    records = cursor3.fetchall()
    cursor3.close()
    print(f"\nBob's health records:")
    if records:
        for r in records:
            print(f"  ID: {r['reading_id']}, Value: {r['value']}, Date: {r['date_time']}, Status: {r['status']}")
    else:
        print("  No records found!")

conn.close()
