SELECT p.patient_id, p.health_care_number, u.first_name, u.last_name, u.email, u.phone, u.date_of_birth, last_r.last_value, last_r.last_status, last_r.last_date_time
FROM specialists s
JOIN specialistpatient sp ON s.specialist_id = sp.specialist_id
JOIN patients p ON p.patient_id = sp.patient_id
JOIN users u ON u.user_id = p.user_id
LEFT JOIN (
  SELECT r.user_id, r.value AS last_value, r.status AS last_status, r.date_time AS last_date_time
  FROM bloodsugarreadings r
  JOIN (
    SELECT user_id, MAX(date_time) AS max_dt
    FROM bloodsugarreadings
    GROUP BY user_id
  ) x ON x.user_id = r.user_id AND x.max_dt = r.date_time
) AS last_r ON last_r.user_id = u.user_id
WHERE s.working_id = 'jsmith'
ORDER BY u.last_name, u.first_name;
