-- GarageGuide database tests. Run on garageguide_test after 01 and 02.
-- Execute the WHOLE file. Failures raise an exception; successes appear below.
-- Fixtures and temporary helpers roll back. Generated identity sequences can
-- advance even on rollback, so use a separate test database.
BEGIN;
SET LOCAL search_path = public, pg_temp;
CREATE TEMP TABLE gg_test_results (test_id text, feature_id text, test_name text, result text);
CREATE FUNCTION pg_temp.gg_assert(test_id text, feature_id text, test_name text, passed boolean)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF passed IS DISTINCT FROM TRUE THEN
   RAISE EXCEPTION 'FAIL %: %', test_id, test_name;
 END IF;
 INSERT INTO gg_test_results VALUES(test_id, feature_id, test_name, 'PASS');
END $$;
CREATE FUNCTION pg_temp.gg_reject(test_id text, feature_id text, test_name text, statement text, expected_state text)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE actual_state text;
BEGIN
 BEGIN
   EXECUTE statement;
 EXCEPTION WHEN OTHERS THEN
   GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE;
 END;
 IF actual_state IS DISTINCT FROM expected_state THEN
   RAISE EXCEPTION 'FAIL %: % (expected %, got %)', test_id, test_name, expected_state, COALESCE(actual_state,'no rejection');
 END IF;
 INSERT INTO gg_test_results VALUES(test_id, feature_id, test_name, 'PASS');
END $$;

-- Synthetic records only. These hashes are NOT working passwords or tokens.
INSERT INTO users(id,email,password_hash) OVERRIDING SYSTEM VALUE VALUES
 (-9101,'a@fixture.invalid','fixture-not-a-password-hash'),
 (-9102,'b@fixture.invalid','fixture-not-a-password-hash');
INSERT INTO vehicles(id,user_id,year,make,model,vehicle_type,engine,mileage,operating_hours)
OVERRIDING SYSTEM VALUE VALUES
 (-9101,-9101,2020,'Fixture','Car','car','TEST',10000,NULL),
 (-9102,-9102,2020,'Fixture','Bike','dirt bike','TEST',NULL,40),
 (-9103,-9101,2020,'Fixture','Empty','car','TEST',0,NULL);
INSERT INTO service_records(id,vehicle_id,service_date,service_type,description,cost,mileage)
OVERRIDING SYSTEM VALUE VALUES
 (-9101,-9101,'2026-10-01','maintenance','Fixture oil change',60,10000),
 (-9102,-9101,'2026-10-02','repair','Fixture repair',40,10000),
 (-9103,-9101,'2026-10-03','inspection','Fixture free inspection',0,10000),
 (-9104,-9101,'2026-10-04','diagnostic','Fixture unknown cost',NULL,10000),
 (-9105,-9102,'2026-10-01','maintenance','Other owner service',200,NULL);
INSERT INTO maintenance_schedules(id,vehicle_id,name,interval_miles,baseline_mileage,interval_days,baseline_date,interval_hours,baseline_hours)
OVERRIDING SYSTEM VALUE VALUES
 (-9101,-9101,'Oil',5000,10000,NULL,NULL,NULL,NULL),
 (-9102,-9101,'Inspection',NULL,NULL,30,'2026-10-01',NULL,NULL),
 (-9103,-9102,'Hours',NULL,NULL,NULL,NULL,20,40);
INSERT INTO maintenance_completions(vehicle_id,schedule_id,service_record_id) VALUES
 (-9101,-9101,-9101),(-9101,-9102,-9101);
INSERT INTO parts(id,manufacturer,part_number,name,category) OVERRIDING SYSTEM VALUE
 VALUES(-9101,'Fixture','TEST-ONLY','Synthetic filter','filter');
INSERT INTO part_fitments(id,part_id,year,make,model,engine,source_url,verified_on)
OVERRIDING SYSTEM VALUE VALUES
 (-9101,-9101,2020,'Fixture','Car','TEST','https://example.invalid/test-only','2026-10-24');
INSERT INTO saved_parts(id,vehicle_id,part_id,origin,name,part_number) OVERRIDING SYSTEM VALUE VALUES
 (-9101,-9101,-9101,'catalog','Synthetic filter','TEST-ONLY'),
 (-9102,-9101,NULL,'manual','Synthetic manual part','MANUAL-TEST');
INSERT INTO service_parts(id,service_record_id,part_id,name,part_number) OVERRIDING SYSTEM VALUE VALUES
 (-9101,-9101,-9101,'Historical filter snapshot','TEST-ONLY');

SELECT pg_temp.gg_reject('DB01', 'F01, F16', 'Reject duplicate email', 'INSERT INTO users(email,password_hash) VALUES (''a@fixture.invalid'',''fixture'')', '23505');
SELECT pg_temp.gg_reject('DB02', 'F01', 'Require normalized email', 'INSERT INTO users(email,password_hash) VALUES (''UPPER@fixture.invalid'',''fixture'')', '23514');
SELECT pg_temp.gg_reject('DB03', 'F16', 'Reject ownerless vehicle', 'INSERT INTO vehicles(user_id,year,make,model,vehicle_type) VALUES (-99999,2020,''Test'',''Test'',''car'')', '23503');
SELECT pg_temp.gg_reject('DB04', 'F04', 'Reject negative mileage', 'UPDATE vehicles SET mileage=-1 WHERE id=-9101', '23514');
SELECT pg_temp.gg_reject('DB05', 'F04', 'Reject negative hours', 'UPDATE vehicles SET operating_hours=-1 WHERE id=-9102', '23514');
SELECT pg_temp.gg_reject('DB06', 'F06', 'Reject negative cost', 'UPDATE service_records SET cost=-1 WHERE id=-9101', '23514');
SELECT pg_temp.gg_reject('DB07', 'F06', 'Reject unsupported service type', 'UPDATE service_records SET service_type=''other'' WHERE id=-9101', '23514');
SELECT pg_temp.gg_reject('DB08', 'F06', 'Reject empty description', 'UPDATE service_records SET description='' '' WHERE id=-9101', '23514');
SELECT pg_temp.gg_reject('DB09', 'F08', 'Require an interval', 'INSERT INTO maintenance_schedules(vehicle_id,name) VALUES (-9101,''No interval'')', '23514');
SELECT pg_temp.gg_reject('DB10', 'F08', 'Require matching baseline', 'INSERT INTO maintenance_schedules(vehicle_id,name,interval_hours) VALUES (-9102,''No baseline'',20)', '23514');
SELECT pg_temp.gg_reject('DB11', 'F08', 'Reject zero interval', 'UPDATE maintenance_schedules SET interval_miles=0 WHERE id=-9101', '23514');
SELECT pg_temp.gg_reject('DB12', 'F10', 'Reject duplicate completion', 'INSERT INTO maintenance_completions(vehicle_id,schedule_id,service_record_id) VALUES (-9101,-9101,-9101)', '23505');
SELECT pg_temp.gg_reject('DB13', 'F10, F16', 'Reject cross-vehicle completion', 'INSERT INTO maintenance_completions(vehicle_id,schedule_id,service_record_id) VALUES (-9101,-9101,-9105)', '23503');
SELECT pg_temp.gg_reject('DB14', 'F12', 'Reject duplicate saved catalog part', 'INSERT INTO saved_parts(vehicle_id,part_id,origin,name,part_number) VALUES(-9101,-9101,''catalog'',''Test'',''TEST-ONLY'')', '23505');
SELECT pg_temp.gg_reject('DB15', 'F12', 'Reject manual origin with catalog ID', 'UPDATE saved_parts SET origin=''manual'' WHERE id=-9101', '23514');
SELECT pg_temp.gg_reject('DB16', 'F11', 'Reject fitment without source', 'UPDATE part_fitments SET source_url='''' WHERE id=-9101', '23514');
SELECT pg_temp.gg_reject('DB17', 'F11', 'Reject duplicate manufacturer/part number', 'INSERT INTO parts(manufacturer,part_number,name,category) VALUES (''Fixture'',''TEST-ONLY'',''Test'',''filter'')', '23505');
SELECT pg_temp.gg_reject('DB18', 'F02, F03', 'Require session expiration after creation', 'INSERT INTO user_sessions(user_id,token_hash,created_at,expires_at) VALUES(-9101,''fixture-token'',''2026-10-24'',''2026-10-23'')', '23514');
SELECT pg_temp.gg_reject('DB19', 'F16', 'Protect parent with service history', 'DELETE FROM vehicles WHERE id=-9101', '23503');
SELECT pg_temp.gg_reject('DB20', 'F06', 'Reject zero replacement quantity', 'UPDATE service_parts SET quantity=0 WHERE id=-9101', '23514');
SELECT pg_temp.gg_assert('DB21', 'F04, F05', 'Retain separate miles and hours', ((SELECT mileage=10000 AND operating_hours IS NULL FROM vehicles WHERE id=-9101) AND (SELECT mileage IS NULL AND operating_hours=40 FROM vehicles WHERE id=-9102)));
SELECT pg_temp.gg_assert('DB22', 'F06, F13', 'Keep unknown and zero distinct', ((SELECT cost IS NULL FROM service_records WHERE id=-9104) AND (SELECT cost=0 FROM service_records WHERE id=-9103)));
SELECT pg_temp.gg_assert('DB23', 'F13', 'Known total and unknown count', ((SELECT recorded_total_usd=100 AND unknown_cost_count=1 AND service_count=4 FROM vehicle_expense_summary WHERE vehicle_id=-9101)));
SELECT pg_temp.gg_assert('DB24', 'F13', 'Separate vehicle totals', ((SELECT recorded_total_usd=200 FROM vehicle_expense_summary WHERE vehicle_id=-9102)));
SELECT pg_temp.gg_assert('DB25', 'F13, F15', 'Empty vehicle remains visible', ((SELECT recorded_total_usd=0 AND service_count=0 AND unknown_cost_count=0 FROM vehicle_expense_summary WHERE vehicle_id=-9103)));
SELECT pg_temp.gg_assert('DB26', 'F08', 'Store date and hours schedules', ((SELECT baseline_date + interval_days = DATE '2026-10-31' FROM maintenance_schedules WHERE id=-9102) AND (SELECT baseline_hours + interval_hours=60 FROM maintenance_schedules WHERE id=-9103)));
SELECT pg_temp.gg_assert('DB27', 'F10, F13', 'Multiple completion links do not multiply expenses', ((SELECT COUNT(*)=2 FROM maintenance_completions WHERE service_record_id=-9101) AND (SELECT recorded_total_usd=100 FROM vehicle_expense_summary WHERE vehicle_id=-9101)));
SELECT pg_temp.gg_assert('DB28', 'F11', 'Exact catalog lookup returns fixture', ((SELECT COUNT(*)=1 FROM parts p JOIN part_fitments f ON f.part_id=p.id WHERE f.year=2020 AND f.make='Fixture' AND f.model='Car' AND f.engine='TEST' AND p.part_number='TEST-ONLY')));

UPDATE vehicles SET mileage=12000 WHERE id=-9101;
SELECT pg_temp.gg_assert('DB29', 'F05', 'Current reading does not rewrite history', ((SELECT mileage=10000 FROM service_records WHERE id=-9101)));

UPDATE service_records SET cost=50 WHERE id=-9102;
SELECT pg_temp.gg_assert('DB30', 'F07, F13', 'Expense view reflects edit', ((SELECT recorded_total_usd=110 FROM vehicle_expense_summary WHERE vehicle_id=-9101)));

DELETE FROM saved_parts WHERE id=-9101;
SELECT pg_temp.gg_assert('DB31', 'F07, F12', 'Removing saved part preserves history', ((SELECT name='Historical filter snapshot' FROM service_parts WHERE id=-9101)));

DELETE FROM part_fitments WHERE part_id=-9101; DELETE FROM parts WHERE id=-9101;
SELECT pg_temp.gg_assert('DB32', 'F12', 'Removing catalog part preserves snapshot', ((SELECT part_id IS NULL AND part_number='TEST-ONLY' FROM service_parts WHERE id=-9101)));

DELETE FROM service_records WHERE id=-9101;
SELECT pg_temp.gg_assert('DB33', 'F07, F10, F13', 'Service deletion cleans links and updates expenses', (NOT EXISTS(SELECT 1 FROM maintenance_completions WHERE service_record_id=-9101) AND NOT EXISTS(SELECT 1 FROM service_parts WHERE service_record_id=-9101) AND (SELECT recorded_total_usd=50 FROM vehicle_expense_summary WHERE vehicle_id=-9101)));

INSERT INTO user_sessions(user_id,token_hash,created_at,expires_at) VALUES(-9101,'fixture-hash','2026-10-24','2026-10-25'); UPDATE user_sessions SET revoked_at='2026-10-24 12:00:00+00' WHERE token_hash='fixture-hash';
SELECT pg_temp.gg_assert('DB34', 'F03', 'Session revocation can be stored', ((SELECT revoked_at IS NOT NULL FROM user_sessions WHERE token_hash='fixture-hash')));

SELECT * FROM gg_test_results ORDER BY test_id;
SELECT COUNT(*) AS passed_tests, 'All tests passed; fixtures rolled back below' AS summary FROM gg_test_results;
ROLLBACK;

