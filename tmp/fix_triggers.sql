DROP TRIGGER IF EXISTS trg_classify_reading;
DELIMITER $$
CREATE TRIGGER `trg_classify_reading` BEFORE INSERT ON `bloodsugarreadings` FOR EACH ROW
BEGIN
  DECLARE nmin DECIMAL(5,2); DECLARE nmax DECIMAL(5,2);
  DECLARE bmin DECIMAL(5,2); DECLARE bmax DECIMAL(5,2);

  SELECT min_value, max_value INTO nmin, nmax
    FROM thresholds
   WHERE user_id = NEW.user_id AND status = 'normal'
   ORDER BY created_at DESC LIMIT 1;

  SELECT min_value, max_value INTO bmin, bmax
    FROM thresholds
   WHERE user_id = NEW.user_id AND status = 'borderline'
   ORDER BY created_at DESC LIMIT 1;

  IF nmin IS NOT NULL AND nmax IS NOT NULL THEN
    IF NEW.value BETWEEN nmin AND nmax THEN
      SET NEW.status = 'normal';
    ELSEIF bmin IS NOT NULL AND bmax IS NOT NULL AND NEW.value BETWEEN bmin AND bmax THEN
      SET NEW.status = 'borderline';
    ELSE
      SET NEW.status = 'abnormal';
    END IF;
  END IF;
END
$$
DELIMITER ;
