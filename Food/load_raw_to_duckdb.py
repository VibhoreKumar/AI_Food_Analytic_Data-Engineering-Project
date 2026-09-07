"""
Loads raw CSV files into a DuckDB database, creating a RAW schema
that mirrors what previously lived in Snowflake's ZOMATO.RAW schema.
"""

import duckdb
import os

DB_PATH = "zomato.duckdb"
DATA_DIR = "../data"

TABLES = {
    "restaurants": "restaurant.csv",
    "users": "users.csv",
    "food": "food.csv",
    "menu": "menu.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
    "reviews": "reviews.csv",
}

def main():
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    for table_name, csv_file in TABLES.items():
        csv_path = os.path.join(DATA_DIR, csv_file)
        if not os.path.exists(csv_path):
            print(f"SKIP {table_name} - file not found at {csv_path}")
            continue

        print(f"Loading {csv_file} -> raw.{table_name} ...")
        try:
            con.execute(f"""
                CREATE OR REPLACE TABLE raw.{table_name} AS
                SELECT * FROM read_csv_auto('{csv_path}', header=True)
            """)
        except Exception as e:
            print(f"  Type detection failed, retrying with all columns as VARCHAR...")
            con.execute(f"""
                CREATE OR REPLACE TABLE raw.{table_name} AS
                SELECT * FROM read_csv_auto('{csv_path}', header=True, all_varchar=True)
            """)

        count = con.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
        print(f"  -> {count:,} rows loaded")

    con.close()
    print("\nDone. All raw tables loaded into DuckDB.")


if __name__ == "__main__":
    main()
