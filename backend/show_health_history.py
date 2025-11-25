"""Show health history summary for all users"""
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Get all patients with their health reading counts
query = """
SELECT 
    p.patient_id,
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    COUNT(b.reading_id) as total_readings,
    MIN(b.date_time) as first_reading,
    MAX(b.date_time) as last_reading,
    ROUND(AVG(b.value), 1) as avg_blood_sugar,
    MIN(b.value) as min_blood_sugar,
    MAX(b.value) as max_blood_sugar
FROM patients p
JOIN users u ON p.user_id = u.user_id
LEFT JOIN bloodsugarreadings b ON u.user_id = b.user_id
GROUP BY p.patient_id, u.user_id, u.first_name, u.last_name, u.email
ORDER BY p.patient_id
"""

cursor.execute(query)
patients = cursor.fetchall()

print("=" * 120)
print("PATIENT HEALTH HISTORY SUMMARY")
print("=" * 120)
print(f"{'ID':<5} {'Name':<25} {'Email':<30} {'Readings':<10} {'Avg BS':<10} {'Range':<15} {'Last Reading'}")
print("-" * 120)

for p in patients:
    name = f"{p['first_name']} {p['last_name']}"
    readings = p['total_readings']
    avg_bs = f"{p['avg_blood_sugar']}" if p['avg_blood_sugar'] else "-"
    bs_range = f"{p['min_blood_sugar']}-{p['max_blood_sugar']}" if p['min_blood_sugar'] else "-"
    last_reading = p['last_reading'].strftime("%Y-%m-%d") if p['last_reading'] else "-"
    
    print(f"{p['patient_id']:<5} {name:<25} {p['email']:<30} {readings:<10} {avg_bs:<10} {bs_range:<15} {last_reading}")

print("-" * 120)
print(f"\nTotal Patients: {len(patients)}")
print(f"Total Readings: {sum(p['total_readings'] for p in patients)}")

# Show detailed breakdown by status
print("\n" + "=" * 120)
print("READING STATUS BREAKDOWN")
print("=" * 120)

cursor.execute("""
    SELECT 
        p.patient_id,
        u.first_name,
        u.last_name,
        SUM(CASE WHEN b.status = 'normal' THEN 1 ELSE 0 END) as normal_count,
        SUM(CASE WHEN b.status = 'borderline' THEN 1 ELSE 0 END) as borderline_count,
        SUM(CASE WHEN b.status = 'abnormal' THEN 1 ELSE 0 END) as abnormal_count,
        COUNT(b.reading_id) as total
    FROM patients p
    JOIN users u ON p.user_id = u.user_id
    LEFT JOIN bloodsugarreadings b ON u.user_id = b.user_id
    GROUP BY p.patient_id, u.first_name, u.last_name
    HAVING total > 0
    ORDER BY p.patient_id
""")

status_data = cursor.fetchall()

print(f"{'ID':<5} {'Name':<25} {'Normal':<10} {'Borderline':<12} {'Abnormal':<10} {'Total':<10} {'Health %'}")
print("-" * 120)

for s in status_data:
    name = f"{s['first_name']} {s['last_name']}"
    normal = s['normal_count']
    borderline = s['borderline_count']
    abnormal = s['abnormal_count']
    total = s['total']
    health_pct = f"{(normal/total*100):.1f}%" if total > 0 else "-"
    
    print(f"{s['patient_id']:<5} {name:<25} {normal:<10} {borderline:<12} {abnormal:<10} {total:<10} {health_pct}")

cursor.close()
conn.close()
