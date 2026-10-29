-- Run after 01_schema.sql. This view reads live data; it stores no duplicate costs.
CREATE OR REPLACE VIEW vehicle_expense_summary AS
SELECT v.id AS vehicle_id,
       v.user_id,
       COUNT(s.id) AS service_count,
       COALESCE(SUM(s.cost), 0::numeric) AS recorded_total_usd,
       COUNT(s.id) FILTER (WHERE s.cost IS NULL) AS unknown_cost_count
FROM vehicles v
LEFT JOIN service_records s ON s.vehicle_id = v.id
GROUP BY v.id, v.user_id;

-- This view is NOT an authorization boundary. FastAPI must filter by the
-- authenticated user_id; never accept a claimed owner ID from the client.
