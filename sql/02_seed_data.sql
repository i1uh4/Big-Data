-- Заполнение wells
INSERT INTO wells (well_name, field, region, start_date) VALUES
('W-001','North','Siberia','2020-01-01'),
('W-002','North','Siberia','2020-03-10'),
('W-003','South','Volga','2019-07-15'),
('W-004','East','Ural','2021-05-20'),
('W-005','West','Siberia','2022-02-01');

-- Production: 90 дней по каждой скважине
INSERT INTO production (well_id, prod_date, oil_volume, gas_volume, water_cut)
SELECT
    w.well_id,
    d::date,
    ROUND((random()*100 + 50)::numeric, 2),
    ROUND((random()*200 + 100)::numeric, 2),
    ROUND((random()*30)::numeric, 2)
FROM wells w
CROSS JOIN generate_series(CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE, '1 day') d;

-- Telemetry: каждый час по 30 дней
INSERT INTO telemetry (well_id, ts, pressure, temperature, power, pump_runtime, downtime)
SELECT
    w.well_id,
    ts,
    ROUND((random()*50 + 100)::numeric, 2),
    ROUND((random()*30 + 50)::numeric, 2),
    ROUND((random()*100 + 200)::numeric, 2),
    ROUND((random()*24)::numeric, 2),
    ROUND((random()*5)::numeric, 2)
FROM wells w
CROSS JOIN generate_series(CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE, '1 hour') ts;

-- Well targets
INSERT INTO well_targets (well_id, target_date, target_volume)
SELECT well_id, d::date, ROUND((random()*120 + 60)::numeric, 2)
FROM wells
CROSS JOIN generate_series(CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE, '1 day') d;

-- Pump sensors
INSERT INTO pump_sensors (pump_id, ts, vibration, temperature, current_a, rpm)
SELECT
    p,
    ts,
    ROUND((random()*5 + 1)::numeric, 3),
    ROUND((random()*40 + 40)::numeric, 2),
    ROUND((random()*20 + 5)::numeric, 2),
    (random()*1500 + 1000)::int
FROM generate_series(1,5) p
CROSS JOIN generate_series(CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE, '2 hours') ts;

-- Pump failures
INSERT INTO pump_failures (pump_id, fail_ts, fail_type) VALUES
(1, CURRENT_DATE - INTERVAL '20 days', 'overheat'),
(2, CURRENT_DATE - INTERVAL '15 days', 'vibration'),
(3, CURRENT_DATE - INTERVAL '10 days', 'mechanical'),
(1, CURRENT_DATE - INTERVAL '5 days', 'electrical');

-- Deliveries
INSERT INTO deliveries (delivery_date, driver, route, distance_km, volume_t, cost, delay_min, weather)
SELECT
    d::date,
    (ARRAY['Ivanov','Petrov','Sidorov','Kozlov'])[floor(random()*4+1)],
    'Route-' || floor(random()*10+1),
    ROUND((random()*500 + 50)::numeric, 2),
    ROUND((random()*30 + 5)::numeric, 2),
    ROUND((random()*10000 + 2000)::numeric, 2),
    floor(random()*120)::int,
    (ARRAY['sunny','rain','snow','fog','storm'])[floor(random()*5+1)]
FROM generate_series(CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE, '1 day') d;