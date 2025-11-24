SELECT
    p.patient_id,
    p.health_care_number,
    u.first_name,
    u.last_name,
    u.email,
    u.phone,
    u.date_of_birth,
    (
      SELECT rr.value
      FROM bloodsugarreadings rr
      WHERE rr.user_id = u.user_id
      ORDER BY rr.date_time DESC
      LIMIT 1
    ) AS last_value,
    (
      SELECT rr.status
      FROM bloodsugarreadings rr
      WHERE rr.user_id = u.user_id
      ORDER BY rr.date_time DESC
      LIMIT 1
    ) AS last_status,
    (
      SELECT rr.date_time
      FROM bloodsugarreadings rr
      WHERE rr.user_id = u.user_id
      ORDER BY rr.date_time DESC
      LIMIT 1
    ) AS last_date_time
FROM specialists s
JOIN specialistpatient sp ON s.specialist_id = sp.specialist_id
JOIN patients p ON p.patient_id = sp.patient_id
JOIN users u ON u.user_id = p.user_id
WHERE s.working_id = 'jsmith'
ORDER BY u.last_name, u.first_name;
