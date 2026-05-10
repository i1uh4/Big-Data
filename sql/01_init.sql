-- Справочник скважин
CREATE TABLE IF NOT EXISTS wells (
    well_id SERIAL PRIMARY KEY,
    well_name VARCHAR(50),
    field VARCHAR(50),
    region VARCHAR(50),
    start_date DATE
);

-- Ежедневная добыча
CREATE TABLE IF NOT EXISTS production (
    id SERIAL PRIMARY KEY,
    well_id INT REFERENCES wells(well_id),
    prod_date DATE,
    oil_volume NUMERIC(10,2),
    gas_volume NUMERIC(10,2),
    water_cut NUMERIC(5,2)
);

-- Телеметрия
CREATE TABLE IF NOT EXISTS telemetry (
    id SERIAL PRIMARY KEY,
    well_id INT REFERENCES wells(well_id),
    ts TIMESTAMP,
    pressure NUMERIC(8,2),
    temperature NUMERIC(6,2),
    power NUMERIC(8,2),
    pump_runtime NUMERIC(5,2),
    downtime NUMERIC(5,2)
);

-- Целевые параметры
CREATE TABLE IF NOT EXISTS well_targets (
    id SERIAL PRIMARY KEY,
    well_id INT REFERENCES wells(well_id),
    target_date DATE,
    target_volume NUMERIC(10,2)
);

-- Сенсоры насосов
CREATE TABLE IF NOT EXISTS pump_sensors (
    id SERIAL PRIMARY KEY,
    pump_id INT,
    ts TIMESTAMP,
    vibration NUMERIC(6,3),
    temperature NUMERIC(6,2),
    current_a NUMERIC(6,2),
    rpm INT
);

-- Отказы насосов
CREATE TABLE IF NOT EXISTS pump_failures (
    id SERIAL PRIMARY KEY,
    pump_id INT,
    fail_ts TIMESTAMP,
    fail_type VARCHAR(50)
);

-- Поставки
CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    delivery_date DATE,
    driver VARCHAR(50),
    route VARCHAR(100),
    distance_km NUMERIC(8,2),
    volume_t NUMERIC(8,2),
    cost NUMERIC(10,2),
    delay_min INT,
    weather VARCHAR(30)
);