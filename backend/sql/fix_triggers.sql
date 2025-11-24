-- Idempotent trigger recreation for Blood Sugar Monitoring System
-- Drop existing triggers if present, then (re)create them.
-- Run this file inside the database (see README_TRIGGER_FIX.md)

DROP TRIGGER IF EXISTS `trg_bloodsugar_abnormal_alert`;
DROP TRIGGER IF EXISTS `trg_bsr_set_status`;

DELIMITER $$

CREATE TRIGGER `trg_bloodsugar_abnormal_alert`
AFTER INSERT ON `bloodsugarreadings`
FOR EACH ROW
BEGIN
  IF NEW.status = 'abnormal' THEN
    INSERT INTO alerts (user_id, specialist_id, reason)
    VALUES (
      NEW.user_id,
      (SELECT specialist_id
         FROM specialistpatient sp
         JOIN patients p ON sp.patient_id = p.patient_id
        WHERE p.user_id = NEW.user_id
        LIMIT 1),
      CONCAT('Abnormal reading detected: ', NEW.value, ' ', NEW.unit)
    );
  END IF;
END $$

CREATE TRIGGER `trg_bsr_set_status`
BEFORE INSERT ON `bloodsugarreadings`
FOR EACH ROW
BEGIN
  DECLARE v_status VARCHAR(15);

  IF NEW.status IS NULL OR NEW.status = '' THEN
    SELECT t.status
      INTO v_status
      FROM thresholds t
     WHERE t.user_id = NEW.user_id
       AND (t.min_value IS NULL OR NEW.value >= t.min_value)
       AND (t.max_value IS NULL OR NEW.value <= t.max_value)
     ORDER BY FIELD(t.status, 'abnormal','borderline','normal')
     LIMIT 1;

    IF v_status IS NULL THEN
      SET v_status = 'normal';
    END IF;

    SET NEW.status = v_status;
  END IF;
END $$

DELIMITER ;
