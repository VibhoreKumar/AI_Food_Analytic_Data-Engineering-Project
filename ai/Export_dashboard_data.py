"""
Exports DuckDB marts data to JSON files for the static HTML dashboard.
"""

import json
import os
import duckdb

DB_PATH = "../Food/zomato.duckdb"
OUTPUT_DIR = "../web_dashboard/data"

def export_query(con, query, filename):
    result = con.execute(query)
    columns = [desc[0] for desc in result.description]
    rows = [dict(zip(columns, row)) for row in result.fetchall()]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f"{OUTPUT_DIR}/{filename}.json"
    with open(path, "w") as f:
        json.dump(rows, f, default=str, indent=2)
    print(f"Exported {len(rows)} rows -> {path}")


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    export_query(con, "SELECT * FROM marts.mart_daily_city_revenune ORDER BY month", "city_revenue")
    export_query(con, "SELECT * FROM marts.mart_delivery_sla", "delivery_sla")
    export_query(con, "SELECT * FROM marts.mart_restaurant_performance ORDER BY revenue DESC LIMIT 20", "restaurant_performance")
    export_query(con, """
        SELECT
            (SELECT COUNT(*) FROM raw.reviews) AS total_reviews,
            (SELECT COUNT(*) FROM raw.restaurants) AS total_restaurants,
            (SELECT COUNT(*) FROM raw.orders) AS total_orders,
            (SELECT COUNT(*) FROM raw.users) AS total_users
    """, "summary_stats")

    con.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
