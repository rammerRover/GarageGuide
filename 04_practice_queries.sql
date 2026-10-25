-- Optional SQL practice on garageguide_test, after schema and views.
-- All example data is rolled back at the end. Run the entire script.
BEGIN;

-- INSERT creates a row. RETURNING shows the generated primary key.
-- This is a fake password hash, not a login-ready account.
INSERT INTO users(email,password_hash)
VALUES ('practice@garageguide.invalid','NOT-A-REAL-PASSWORD-HASH')
RETURNING id, email;

INSERT INTO vehicles(user_id,year,make,model,engine,vehicle_type,mileage)
SELECT id,1995,'Land Rover','Discovery','Example engine','car',100000
FROM users WHERE email='practice@garageguide.invalid'
RETURNING id, user_id, make, model;

INSERT INTO service_records(vehicle_id,service_date,service_type,description,cost,mileage)
SELECT v.id,CURRENT_DATE,'maintenance','Practice oil change',60,100000
FROM vehicles v JOIN users u ON u.id=v.user_id
WHERE u.email='practice@garageguide.invalid';

-- SELECT reads rows; JOIN follows the foreign-key relationship.
SELECT v.id,v.year,v.make,v.model,s.service_date,s.description,s.cost
FROM vehicles v
JOIN users u ON u.id=v.user_id
LEFT JOIN service_records s ON s.vehicle_id=v.id
WHERE u.email='practice@garageguide.invalid'
ORDER BY s.service_date DESC;

-- A view is a saved query. It reads current data each time you select it.
SELECT e.* FROM vehicle_expense_summary e
JOIN users u ON u.id=e.user_id WHERE u.email='practice@garageguide.invalid';

-- UPDATE changes only rows matching WHERE. Never omit WHERE accidentally.
UPDATE vehicles SET mileage=101000, readings_updated_at=CURRENT_TIMESTAMP
WHERE user_id=(SELECT id FROM users WHERE email='practice@garageguide.invalid');

-- Current mileage is 101000; the earlier service still records 100000.
SELECT v.mileage AS current_mileage, s.mileage AS historical_mileage
FROM vehicles v JOIN service_records s ON s.vehicle_id=v.id
JOIN users u ON u.id=v.user_id WHERE u.email='practice@garageguide.invalid';

-- ROLLBACK undoes this practice session. COMMIT would retain the changes.
ROLLBACK;
