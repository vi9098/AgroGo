import csv
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "agrigo.db"
CSV_PATH = Path(r"C:\Users\raika\Downloads\mynew\crop-wise-area-production-yield.csv")

def setup_tables(conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS crop_production_historical (
        id INTEGER PRIMARY KEY,
        year TEXT,
        state_name TEXT,
        state_code INTEGER,
        district_name TEXT,
        district_code INTEGER,
        crop_name TEXT,
        crop_code REAL,
        crop_type TEXT,
        season TEXT,
        area REAL,
        area_unit TEXT,
        production REAL,
        production_unit TEXT,
        yield REAL,
        yield_unit TEXT
    )
    """)
    conn.commit()

def create_indexes(conn: sqlite3.Connection):
    c = conn.cursor()
    print("Creating SQLite indexes for ultra-fast query latency...", flush=True)
    c.execute("CREATE INDEX IF NOT EXISTS idx_cph_state_crop ON crop_production_historical(state_name, crop_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cph_dist_crop ON crop_production_historical(district_name, crop_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cph_crop ON crop_production_historical(crop_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cph_state ON crop_production_historical(state_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cph_district ON crop_production_historical(district_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cph_season ON crop_production_historical(season)")
    conn.commit()
    print("Indexes created successfully.", flush=True)

def build_district_benchmarks(conn: sqlite3.Connection):
    print("Building district-level crop benchmarks table...", flush=True)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS district_crop_benchmarks AS
    SELECT 
        state_name,
        district_name,
        crop_name,
        crop_type,
        season,
        ROUND(AVG(yield), 3) as avg_yield,
        ROUND(MAX(yield), 3) as max_yield,
        ROUND(MIN(yield), 3) as min_yield,
        ROUND(AVG(production), 2) as avg_production,
        ROUND(AVG(area), 2) as avg_area,
        COUNT(*) as record_count
    FROM crop_production_historical
    WHERE yield IS NOT NULL AND yield > 0
    GROUP BY state_name, district_name, crop_name, season;
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_dcb_lookup ON district_crop_benchmarks(state_name, district_name, crop_name);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_dcb_crop ON district_crop_benchmarks(crop_name);")
    conn.commit()
    print("District crop benchmarks table ready!", flush=True)

def ingest_data():
    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} not found!", flush=True)
        return

    conn = sqlite3.connect(DB_PATH)
    setup_tables(conn)

    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM crop_production_historical")
    existing = c.fetchone()[0]
    if existing > 400000:
        print(f"Dataset already ingested ({existing} rows in crop_production_historical).", flush=True)
        conn.close()
        return

    print(f"Starting ingestion of {CSV_PATH} into SQLite...", flush=True)
    t0 = time.time()

    insert_sql = """
    INSERT INTO crop_production_historical 
    (id, year, state_name, state_code, district_name, district_code, crop_name, crop_code, crop_type, season, area, area_unit, production, production_unit, yield, yield_unit)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    batch = []
    batch_size = 25000
    total = 0

    with open(CSV_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = next(reader) # skip header
        
        c.execute("PRAGMA synchronous = OFF;")
        c.execute("PRAGMA journal_mode = MEMORY;")
        c.execute("BEGIN TRANSACTION;")

        for row in reader:
            if not row or len(row) < 16:
                continue
            try:
                rec_id = int(row[0]) if row[0] else None
                year = row[1].strip()
                state_name = row[2].strip()
                state_code = int(row[3]) if row[3] and row[3].isdigit() else None
                dist_name = row[4].strip()
                dist_code = int(row[5]) if row[5] and row[5].isdigit() else None
                crop_name = row[6].strip()
                crop_code = float(row[7]) if row[7] else None
                crop_type = row[8].strip()
                season = row[9].strip()
                area = float(row[10]) if row[10] else None
                area_unit = row[11].strip()
                production = float(row[12]) if row[12] else None
                prod_unit = row[13].strip()
                yld = float(row[14]) if row[14] else None
                yld_unit = row[15].strip()

                batch.append((rec_id, year, state_name, state_code, dist_name, dist_code, crop_name, crop_code, crop_type, season, area, area_unit, production, prod_unit, yld, yld_unit))
                total += 1

                if len(batch) >= batch_size:
                    c.executemany(insert_sql, batch)
                    batch.clear()
                    print(f" -> Ingested {total:,} rows...", flush=True)
            except Exception as e:
                continue

        if batch:
            c.executemany(insert_sql, batch)
            batch.clear()

        conn.commit()

    create_indexes(conn)
    build_district_benchmarks(conn)

    conn.close()
    elapsed = round(time.time() - t0, 2)
    print(f"Ingestion complete: {total:,} rows ingested in {elapsed}s!", flush=True)

if __name__ == "__main__":
    ingest_data()
