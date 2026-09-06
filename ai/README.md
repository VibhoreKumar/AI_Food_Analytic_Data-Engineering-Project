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

3. Run locally from the `ai` folder:
   ```bash
   cd ai
   streamlit run app.py
   ```

4. For Streamlit Cloud, set the same Snowflake environment variables in the app secrets instead of relying on a local `.env` file.

## Notes

- The app reads raw review data from `ZOMATO.RAW.REVIEWS` and enrichment results from `ZOMATO.AI.REVIEW_ENRICHED`.
