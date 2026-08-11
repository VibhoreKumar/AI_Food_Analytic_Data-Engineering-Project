# Zomato Snowflake Dashboard

A simple Streamlit dashboard that connects to Snowflake and shows review analytics.

## Setup

1. Install dependencies:
   ```bash
   cd ai
   pip install -r requirements.txt
   ```

2. Ensure Snowflake credentials are available in `ai/.env` or in your environment:
   - `SNOWFLAKE_ACCOUNT`
   - `SNOWFLAKE_USER`
   - `SNOWFLAKE_PASSWORD`
   - `SNOWFLAKE_WAREHOUSE` (default: `ZOMATO_WH`)
   - `SNOWFLAKE_DATABASE` (default: `ZOMATO`)
   - `SNOWFLAKE_SCHEMA` (default: `RAW`)

3. Run locally:
   ```bash
   streamlit run app.py
   ```

## Notes

- The app reads raw review data from `ZOMATO.RAW.REVIEWS` and enrichment results from `ZOMATO.AI.REVIEW_ENRICHED`.
