# Zomato Snowflake Dashboard

A simple Streamlit app that connects to Snowflake and displays review metrics, sentiment breakdowns, topic trends, and latest enriched reviews.

## Setup

1. Install dependencies:
   ```bash
   cd ai
   pip install -r requirements.txt
   ```

2. Make sure Snowflake credentials are available in `ai/.env` or in your environment:
   - `SNOWFLAKE_ACCOUNT`
   - `SNOWFLAKE_USER`
   - `SNOWFLAKE_PASSWORD`
   - `SNOWFLAKE_WAREHOUSE` (optional, default: `ZOMATO_WH`)
   - `SNOWFLAKE_DATABASE` (optional, default: `ZOMATO`)
   - `SNOWFLAKE_SCHEMA` (optional, default: `RAW`)

3. Run the dashboard:
   ```bash
   streamlit run streamlit_app.py
   ```

## Notes

- The app uses the same Snowflake configuration pattern as `ai/enrich_reviews.py`.
- It reads raw review details from `ZOMATO.RAW.REVIEWS` and enrichment results from `ZOMATO.AI.REVIEW_ENRICHED`.
