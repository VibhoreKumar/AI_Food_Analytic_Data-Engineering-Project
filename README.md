# Food-Delivery Analytics Pipeline 🍽️

An end-to-end data engineering and AI project simulating a food-delivery analytics platform — from raw data ingestion to an AI-enriched, interactive dashboard.

## Overview

This project builds a complete data pipeline on a **medallion architecture** (Bronze → Silver → Gold), orchestrated end-to-end with **Apache Airflow**, enriched with an **AI layer** for automated review sentiment analysis, and surfaced through an interactive **Streamlit** dashboard.

## Architecture

```
S3 (raw files)
   │
   ▼
Snowflake — RAW (Bronze)
   │  COPY INTO
   ▼
dbt — STAGING (Silver)
   │  cleaned, standardized models
   ▼
dbt — MARTS (Gold)
   │  dimensional models + aggregates
   ▼
Gemini API — AI enrichment (review sentiment, topics, issues)
   │
   ▼
Streamlit Dashboard
```

- **Ingestion**: Raw restaurant, order, user, and review data lands in **AWS S3**, secured with custom IAM roles and least-privilege policies
- **Warehouse**: Data loads into **Snowflake** via an external stage (`COPY INTO`), structured across Bronze (raw), Silver (staging), and Gold (marts) layers
- **Transformation**: **dbt** models handle cleaning, testing, and business logic — 17 models covering staging views, dimensions, incremental facts, and aggregated marts
- **AI Enrichment**: A Python service classifies customer review sentiment, topic, and key issues using the **Google Gemini API**, writing structured results back into Snowflake
- **Orchestration**: An **Airflow DAG** (Dockerized) runs the full pipeline on a schedule: `reload_raw → dbt_build_core → enrich_reviews → dbt_build_ai`
- **Presentation**: A **Streamlit** dashboard surfaces sentiment distribution, topic breakdowns, revenue trends, delivery SLAs, and restaurant performance

## Tech Stack

**Cloud & Storage**: AWS S3, AWS IAM
**Warehouse**: Snowflake
**Transformation**: dbt
**Orchestration**: Apache Airflow, Docker
**AI/ML**: Google Gemini API
**Visualization**: Streamlit, Plotly
**Language**: Python, SQL

## Project Structure

```
zomato_ai_project/
├── zomato/                  # dbt project
│   ├── models/
│   │   ├── staging/         # Silver layer — cleaned staging models
│   │   └── marts/           # Gold layer — dimensions, facts, business marts
│   ├── macros/
│   ├── tests/
│   └── dbt_project.yml
├── airflow/                 # Airflow DAG + Docker Compose setup
│   ├── dags/
│   │   └── zomato_batch.py
│   └── docker-compose.yaml
├── ai/                       # AI review enrichment
│   └── enrich_reviews.py    # Gemini API sentiment/topic classification
└── streamlit_app/            # Analytics dashboard
    ├── app.py
    └── requirements.txt
```

## Data Model

**Staging (Silver)** — one-to-one pass-throughs of raw sources: `stg_restaurants`, `stg_users`, `stg_food`, `stg_menu`, `stg_orders`, `stg_order_items`, `stg_reviews`

**Marts (Gold)**:
| Table | Description |
|---|---|
| `dim_restaurants` | Restaurant dimension — name, city, cuisine, rating |
| `dim_customer` | Customer dimension — demographics, segments |
| `dim_food` | Food item dimension |
| `dim_date` | Date dimension |
| `fct_orders` | Incremental order fact table |
| `fact_order_items` | Incremental order line-item fact table |
| `mart_daily_city_revenue` | Daily revenue, orders, AOV by city |
| `mart_delivery_sla` | Delivery performance metrics |
| `mart_restaurant_performance` | Restaurant-level performance ranking |
| `mart_review_insights` | AI-enriched review sentiment and topic aggregates |

## Pipeline Orchestration

The Airflow DAG (`zomato_batch`) runs four tasks in sequence:

1. **`reload_raw`** — loads new files from S3 into Snowflake's raw schema via `COPY INTO`
2. **`dbt_build_core`** — runs all staging and mart models (`dbt build --exclude tag:ai`)
3. **`enrich_reviews`** — runs the Gemini-powered sentiment/topic classification on new reviews
4. **`dbt_build_ai`** — builds the AI-dependent mart (`dbt build --select tag:ai`) using the newly enriched data

## Running Locally

### Prerequisites
- Docker Desktop
- A Snowflake account
- An AWS S3 bucket with a configured storage integration
- A Google Gemini API key

### 1. dbt
```bash
cd zomato
dbt build --exclude tag:ai
```

### 2. Airflow (Dockerized)
```bash
cd airflow
cp .env.example .env   # fill in your credentials
docker compose up -d --build
```
Access the Airflow UI at `http://localhost:8080`.

### 3. AI Enrichment
```bash
cd ai
python3 enrich_reviews.py
```

### 4. Streamlit Dashboard
```bash
cd streamlit_app
streamlit run app.py
```
Access the dashboard at `http://localhost:8501`.

## Key Learnings

- Structuring a warehouse using the medallion architecture for clarity and scalability
- Designing an Airflow DAG with correct task dependencies and failure propagation
- Setting up custom AWS IAM roles and policies for secure, least-privilege cross-service access
- Precisely matching schemas across a multi-layer pipeline — a single mismatched column name can cascade through dozens of downstream models
- Working with LLM APIs for structured data enrichment, and adapting quickly as models and providers evolve
- Debugging real deployment infrastructure — ODBC drivers, secrets management, and cloud hosting trade-offs

## License

This project is for educational and portfolio purposes.
