from models import Database

db = Database()
patients = db.get_all_patients()

print(f"Total patients: {len(patients)}")
print("\nFirst 5 patients:")
for p in patients[:5]:
    print(f"Patient {p['patient_id']}: {p.get('first_name', 'No name')} {p.get('last_name', '')} - Email: {p.get('email', 'NO EMAIL')}")
