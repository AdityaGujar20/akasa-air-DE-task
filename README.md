# Akasa Air — Data Ingestion & KPI Pipeline

* upload daily **customers (CSV)** and **orders (XML)**,
* **clean and append** them to master cleaned files,
* **load** cleaned data into **MySQL** (with upserts),
* compute business **KPIs** from **DB** or **in-memory**, and
* view everything in a **minimal UI** with charts.

---

## What this project does?

1. **Upload**
   You upload two files every day:

   * `customers.csv`
   * `orders.xml`
     They are saved in `data/upload/`.

2. **Clean (Append, not overwrite)**
   When you click **Clean Data**, the app:

   * reads the latest uploaded files,
   * cleans them (trim names, normalize region, parse/validate dates and amounts),
   * and **appends** new rows to two master files:

     * `data/cleaned/customers_cleaned.csv`
     * `data/cleaned/orders_cleaned.csv`
       If these files don’t exist yet, they are created.
       If they do exist, new rows are appended (deduped if needed).

3. **Load to Database (MySQL)**
   When you click **Load to DB**, the app:

   * reads the cleaned CSVs,
   * matches orders to customers by **mobile_number → customer_id**,
   * **upserts** customers and orders into MySQL (so re-running does not duplicate),
   * keeps orders at **SKU level** with `order_id`, `sku_id`, `sku_count`, `total_amount`, `order_date_time`.

4. **KPIs (two ways)**
   You can compute KPIs:

   * **From MySQL** (fast for bigger data, uses SQL)
   * **In-memory** (from cleaned CSVs, uses Pandas)

   KPIs required:

   * **Repeat Customers**: customers with more than one order
   * **Monthly Order Trends**: count orders by month
   * **Regional Revenue**: sum of order totals by region
     (uses “one row per order” logic to avoid double-counting SKU splits)
   * **Top Customers (Last 30 Days)**: highest spenders in the last 30 days

5. **UI Dashboard**
   A simple page at `/ui`:

   * Upload sections (customers, orders)
   * Buttons: **Run Cleaning Pipeline**, **Load to MySQL**
   * KPI tables and charts (bar, line, etc.)
   * After each step, the KPI section refreshes.

---

## Data & file management

* **Raw uploads** land in:

  ```
  data/upload/customers_*.csv
  data/upload/orders_*.xml
  ```

  You can upload new batches every day.

* **Cleaned master files** live in:

  ```
  data/cleaned/customers_cleaned.csv
  data/cleaned/orders_cleaned.csv
  ```

  The cleaning pipeline **appends** new rows to these files.
  We keep all columns from the raw files where possible.
  Standardization we do:

  * customer_name: strip spaces, title case
  * region: strip spaces, title case
  * mobile_number: digits only
  * dates: parsed to timestamps (orders), plus friendly month for trends
  * numerics: `sku_count`, `total_amount` coerced to numbers

* **Database model** (MySQL):

  * `customers(customer_id PK, customer_name, mobile_number, region, created_at)`
  * `orders(order_id PK, customer_id FK, mobile_number, sku_id, sku_count, total_amount, order_date_time, created_at)`
    We upsert on primary keys to avoid duplicates when loading multiple times.

---

## Folder structure (high level)

```
app/
  api/
    upload_routes.py         # upload endpoints
    db_load_routes.py        # load cleaned data into MySQL
    kpi_db_routes.py         # KPIs from DB
    kpi_memory_routes.py     # KPIs from cleaned CSVs (Pandas)
  db/
    connection.py            # SQLAlchemy engine + session
    models.py                # ORM models (Customer, Order)
  ingestion/
    cleaning_pipeline.py     # read upload → clean → append to cleaned/*
    db_loader.py             # read cleaned → upsert into MySQL
  kpi/
    kpi_db.py                # SQL queries for KPIs
    kpi_memory.py            # Pandas KPIs from cleaned CSVs
  ui/
    templates/dashboard.html # UI page
    static/                  
  main.py                    # FastAPI app + router mounts
data/
  upload/                    # raw uploads
  cleaned/                   # master cleaned CSVs (append)
```

---

## Environment variables

Create a `.env` in project root:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=akasa_db
DB_USER=akasa_user
DB_PASSWORD=akasa_pass
```

When running with Docker Compose, `DB_HOST` is usually `mysql`.

---

## Run locally (without Docker)

1. **Clone & enter**

   ```bash
   git clone https://github.com/AdityaGujar20/akasa-air-DE-task.git
   cd akasa-air-DE-task
   ```

2. **Create venv and install**

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Start MySQL**
   Use your local MySQL 8.0 and create `akasa_db`, or run a MySQL container:

   ```bash
   docker run -d --name akasa_mysql \
     -e MYSQL_ROOT_PASSWORD=rootpass \
     -e MYSQL_DATABASE=akasa_db \
     -e MYSQL_USER=akasa_user \
     -e MYSQL_PASSWORD=akasa_pass \
     -p 3306:3306 mysql:8.0
   ```

4. **Create `.env`** (see above).

5. **Run FastAPI**

   ```bash
   uvicorn app.main:app --reload
   ```

6. **Open the app**

   * UI: [http://localhost:8000/ui](http://localhost:8000/ui)
   * Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Run with Docker (recommended)

1. **Docker Compose up**

   ```bash
   docker compose up -d --build
   ```

   This starts:

   * `mysql` (with the right env vars and volume)
   * `fastapi` app (mapped to port `8000`)

2. **Open the app**

   * UI: [http://localhost:8000/ui](http://localhost:8000/ui)
   * Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Volumes**

   * `./data` is mounted into the container so uploads and cleaned files persist.
   * MySQL data is stored in a named Docker volume.

---

## Usage flow (step by step)

1. **Go to UI** → `/ui`
2. **Upload Files**:

   * Choose `customers.csv` and upload
   * Choose `orders.xml` and upload
3. **Clean Data**:

   * Click the **Run Cleaning Pipeline** button
   * This appends the newly cleaned rows to the master CSVs in `data/cleaned/`
4. **Load to DB**:

   * Click **Load to MySQL**
   * This upserts customers and orders into MySQL
5. **View KPIs**:

   * The dashboard shows:

     * Repeat customers (table)
     * Monthly order trends (chart)
     * Regional revenue (chart)
     * Top customers last 30 days (table or chart)
   * You can also hit API endpoints from `/docs`.

You can repeat steps 2–5 every day with new files.
Your cleaned CSVs keep growing; your DB loader safely upserts.

---

## API endpoints (quick reference)

**Uploads**

* `POST /upload/customers` (multipart file)
* `POST /upload/orders` (multipart file)

**Pipeline**

* `POST /clean`
* `POST /db/load`

**KPIs (DB)**

* `GET /kpi/db/repeat-customers`
* `GET /kpi/db/monthly-order-trends`
* `GET /kpi/db/regional-revenue`
* `GET /kpi/db/top-customers?limit=10`

**KPIs (In-memory)**

* `GET /kpi-memory/repeat-customers`
* `GET /kpi-memory/monthly-order-trends`
* `GET /kpi-memory/regional-revenue`
* `GET /kpi-memory/top-customers?limit=10`

---



