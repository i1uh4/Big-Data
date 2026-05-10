# 🛢️ Big Data & ML Pipeline — Аналитика добычи нефти

Полный аналитический pipeline для обработки данных нефтегазовой компании:

```
PostgreSQL → ETL → MinIO → Jupyter (обработка + ML) → Витрины → Superset (BI)
```

Учебный проект по дисциплине **«Семинар наставника — Big Data и ML»**.

---

## 🔧 Стек технологий

| Компонент            | Назначение                                    |
|----------------------|-----------------------------------------------|
| **Docker Compose**   | Оркестрация сервисов                          |
| **PostgreSQL 15**    | OLTP-источник + хранилище витрин              |
| **MinIO**            | S3-совместимое объектное хранилище (parquet)  |
| **JupyterLab**       | Анализ данных, ML                             |
| **Apache Superset 3.1.1** | BI-визуализация                          |
| **Python**           | pandas, sqlalchemy, scikit-learn, pyarrow, boto3, minio |

---

## 🚀 Быстрый старт

### 1. Клонирование

```bash
git clone git@github.com:i1uh4/Big-Data.git
cd bigdata-ml-project
```

### 2. Запуск всей инфраструктуры

```bash
docker-compose up -d --build
```

### 3. Проверка состояния

```bash
docker-compose ps
```

Все сервисы должны быть в статусе `Up`/`running`.

---

## 🌐 Доступ к сервисам

| Сервис      | URL                         | Логин / Пароль          |
|-------------|-----------------------------|-------------------------|
| PostgreSQL  | `localhost:5432`            | admin / admin           |
| MinIO API   | http://localhost:29000      | minioadmin / minioadmin |
| MinIO UI    | http://localhost:29001      | minioadmin / minioadmin |
| JupyterLab  | http://localhost:8888       | token: `jupyter`        |
| Superset    | http://localhost:8088       | admin / admin           |

---

## Пошаговая инструкция выполнения

### Шаг 1. Проверка инфраструктуры

```bash
# Проверить контейнеры
docker-compose ps

# Проверить таблицы в Postgres
docker exec -it postgres psql -U admin -d oilfield -c "\dt"

# Проверить бакеты MinIO (зайдите http://localhost:29001)
# Должны быть: raw, processed, marts
```

### Шаг 2. Запуск ETL (Postgres → MinIO)

```bash
docker-compose run --rm etl python etl_postgres_to_minio.py
```

Ожидаемый вывод:
```
Bucket raw created
Extracted wells: 5 rows
Uploaded raw/wells/data.parquet
Extracted production: 455 rows
Uploaded raw/production/date=YYYY-MM-DD/data.parquet ...
...
ETL completed
```

После: в MinIO (http://localhost:29001) бакет `raw` содержит partitioned parquet-файлы по датам.

### Шаг 3. Data Quality

```bash
docker-compose run --rm etl python data_quality.py
```

Покажет % NULL и количество выбросов по таблицам.

### Шаг 4. Работа в Jupyter

1. Откройте http://localhost:8888 (token: `jupyter`)
2. Запускайте ноутбуки **по порядку**:

| # | Ноутбук                           | Что создаёт                              |
|---|------------------------------------|------------------------------------------|
| 1 | `01_analytics_production.ipynb`    | `mart_daily_production`, `mart_well_kpi`, `mart_production_telemetry` |
| 2 | `02_ml_forecast.ipynb`             | `mart_ml_forecast`, `mart_ml_metrics`    |
| 3 | `03_anomaly_detection.ipynb`       | `mart_anomalies`, `mart_pump_risk`, `mart_failures` |
| 4 | `04_logistics.ipynb`               | `mart_logistics`, `mart_weather_delay`, `mart_driver_kpi`, `mart_route_kpi` |

В каждом ноутбуке: **Run → Run All Cells**.

### Шаг 5. Настройка Apache Superset

#### 5.1. Подключение базы данных

1. Войдите в Superset (admin / admin)
2. **Settings → Database Connections → + DATABASE → PostgreSQL**
3. Перейдите на вкладку **SQLAlchemy URI** и вставьте:
   ```
   //admin0://admin1://admin2://admin3/oilfield
   ```
4. **Display Name:** `Oilfield DB`
5. **TEST CONNECTION** → **CONNECT**


#### 5.2. Датасеты

- `mart_daily_production`
- `mart_well_kpi`
- `mart_production_telemetry`
- `mart_ml_forecast`
- `mart_ml_metrics`
- `mart_anomalies`
- `mart_pump_risk`
- `mart_failures`
- `mart_logistics`
- `mart_weather_delay`
- `mart_driver_kpi`
- `mart_route_kpi`

#### 5.3. Charts

| Chart                      | Dataset                     | Тип          |
|----------------------------|-----------------------------|--------------|
| Daily Oil Production       | `mart_daily_production`     | Line Chart   |
| Top Wells by Avg Oil       | `mart_well_kpi`             | Bar Chart    |
| Pressure vs Oil Heatmap    | `mart_production_telemetry` | Heatmap      |
| Actual vs Predicted        | `mart_ml_forecast`          | Scatter      |
| Error Over Time            | `mart_ml_forecast`          | Line Chart   |
| Vibration Anomalies        | `mart_anomalies`            | Time-series  |
| Risk Score per Pump        | `mart_pump_risk`            | Bar Chart    |
| Delay vs Weather           | `mart_weather_delay`        | Bar Chart    |
| Cost vs Distance           | `mart_logistics`            | Scatter      |
| Driver KPI                 | `mart_driver_kpi`           | Table        |

#### 5.4. Dashboards

1. **Production Analytics** — добыча, KPI скважин, корреляции
2. **ML Forecast** — прогноз vs факт, ошибки модели
3. **Pump Anomalies** — аномалии, risk score, отказы
4. **Logistics** — задержки, KPI водителей, маршруты

---

## 📊 Витрины данных

### `mart_daily_production`
Суточная добыча: `prod_date`, `total_oil`, `total_gas`, `avg_water_cut`

### `mart_well_kpi`
KPI по скважинам: `well_id`, `well_name`, `avg_oil`, `avg_pressure`, `avg_temperature`, `downtime_pct`

### `mart_ml_forecast`
Прогноз дебита: `well_id`, `date`, `actual`, `predicted_rf`, `predicted_lr`, `error`

### `mart_pump_risk`
Риск-скоринг насосов: `pump_id`, `risk_score`, `n_anomalies`, `avg_failure_proba`

### `mart_logistics`, `mart_driver_kpi`, `mart_route_kpi`
Анализ поставок, KPI водителей и эффективность маршрутов.

---

### Полный сброс
```bash
docker-compose down -v   # удаляет volumes (данные)
docker-compose up -d --build
```

---

## 🔧 Полезные команды

```bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker logs -f superset

# Перезапуск одного сервиса
docker-compose restart superset

# Зайти внутрь контейнера
docker exec -it postgres psql -U admin -d oilfield
docker exec -u root -it superset bash

# Список таблиц витрин
docker exec -it postgres psql -U admin -d oilfield -c "\dt mart_*"

# Пересборка ETL после изменения кода
docker-compose build etl
docker-compose run --rm etl python etl_postgres_to_minio.py

# Остановить всё
docker-compose down

# Остановить и удалить данные
docker-compose down -v
```

---

## 📝 Описание данных

| Таблица         | Описание                                              | Объём (~)        |
|-----------------|-------------------------------------------------------|------------------|
| `wells`         | Справочник скважин                                    | 5 строк          |
| `production`    | Ежедневная добыча (oil, gas, water_cut)               | 455 строк        |
| `telemetry`     | Часовая телеметрия (pressure, temp, power, runtime)   | ~3 700 строк     |
| `well_targets`  | Целевые показатели для ML                             | ~305 строк       |
| `pump_sensors`  | Сенсоры насосов (vibration, temp, current, rpm)       | ~1 800 строк     |
| `pump_failures` | Зафиксированные отказы оборудования                   | 4 строки         |
| `deliveries`    | Поставки (маршрут, объём, стоимость, задержка, погода)| ~60 строк        |

---