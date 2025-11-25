"""Show reading counts for all users"""
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Get reading counts for all users
query = """
SELECT 
    u.user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.role,
    COALESCE(COUNT(b.reading_id), 0) as reading_count,
    MIN(b.date_time) as first_reading,
    MAX(b.date_time) as last_reading
FROM users u
LEFT JOIN bloodsugarreadings b ON u.user_id = b.user_id
GROUP BY u.user_id, u.email, u.first_name, u.last_name, u.role
ORDER BY u.role, reading_count DESC, u.user_id
"""

cursor.execute(query)
users = cursor.fetchall()

print("=" * 110)
print("READING COUNTS BY USER")
print("=" * 110)
print(f"{'User ID':<10} {'Role':<12} {'Name':<30} {'Readings':<12} {'Date Range'}")
print("-" * 110)

total_readings = 0
users_with_readings = 0

for u in users:
    name = f"{u['first_name']} {u['last_name']}"
    readings = u['reading_count']
    
    if readings > 0:
        users_with_readings += 1
        first = u['first_reading'].strftime("%Y-%m-%d") if u['first_reading'] else ""
        last = u['last_reading'].strftime("%Y-%m-%d") if u['last_reading'] else ""
        date_range = f"{first} to {last}" if first else ""
    else:
        date_range = "No readings"
    
    total_readings += readings
    
    print(f"{u['user_id']:<10} {u['role']:<12} {name:<30} {readings:<12} {date_range}")

print("-" * 110)
print(f"\nTotal Users: {len(users)}")
print(f"Users with Readings: {users_with_readings}")
print(f"Total Readings: {total_readings}")
print(f"Average per User (with readings): {total_readings/users_with_readings:.1f}" if users_with_readings > 0 else "")

# Breakdown by role
print("\n" + "=" * 110)
print("BREAKDOWN BY ROLE")
print("=" * 110)

cursor.execute("""
    SELECT 
        u.role,
        COUNT(DISTINCT u.user_id) as user_count,
        COUNT(b.reading_id) as total_readings,
        ROUND(AVG(reading_counts.count), 1) as avg_per_user
    FROM users u
    LEFT JOIN bloodsugarreadings b ON u.user_id = b.user_id
    LEFT JOIN (
        SELECT user_id, COUNT(*) as count
        FROM bloodsugarreadings
        GROUP BY user_id
    ) as reading_counts ON u.user_id = reading_counts.user_id
    GROUP BY u.role
    ORDER BY total_readings DESC
""")

role_stats = cursor.fetchall()

print(f"{'Role':<15} {'Users':<10} {'Total Readings':<18} {'Avg per User'}")
print("-" * 110)

for r in role_stats:
    avg = f"{r['avg_per_user']}" if r['avg_per_user'] else "0"
    print(f"{r['role']:<15} {r['user_count']:<10} {r['total_readings']:<18} {avg}")

cursor.close()
conn.close()
