import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor()

# Check Alice's user
cursor.execute("SELECT user_id, email FROM users WHERE email LIKE 'alice%'")
print('Alice user:', cursor.fetchall())

# Check readings count
cursor.execute('SELECT COUNT(*) FROM bloodsugarreadings WHERE user_id = 315')
count = cursor.fetchone()[0]
print(f'Readings count for user_id 315: {count}')

# Check last 5 readings
cursor.execute('SELECT date_time, value, food_intake FROM bloodsugarreadings WHERE user_id = 315 ORDER BY date_time DESC LIMIT 5')
print('Last 5 readings:')
for row in cursor.fetchall():
    print(row)

conn.close()
