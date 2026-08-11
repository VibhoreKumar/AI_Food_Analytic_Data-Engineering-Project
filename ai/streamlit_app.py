import os
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULTS = {
    "warehouse": "ZOMATO_WH",
    "database": "ZOMATO",
    "schema": "RAW",
}


@st.cache_resource
def get_connection():
    snowflake_config = {
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", DEFAULTS["warehouse"]),
        "database": os.getenv("SNOWFLAKE_DATABASE", DEFAULTS["database"]),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", DEFAULTS["schema"]),
    }
    role = os.getenv("SNOWFLAKE_ROLE")
    if role:
        snowflake_config["role"] = role

    missing = [k for k, v in snowflake_config.items() if k in ["user", "password", "account"] and not v]
    if missing:
        raise RuntimeError(
            f"Missing required Snowflake environment variables: {', '.join(missing)}"
        )

    return snowflake.connector.connect(**snowflake_config)


def normalize_rows(cursor, rows):
    columns = [col[0].lower() for col in cursor.description] if cursor.description else []
    return [dict(zip(columns, row)) for row in rows]


@st.cache_data(ttl=60)
def run_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, object]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return normalize_rows(cursor, rows)
    finally:
        cursor.close()


def load_dashboard_data():
    counts = run_query(
        "SELECT COUNT(*) AS total_reviews FROM ZOMATO.RAW.REVIEWS"
    )
    enriched_counts = run_query(
        "SELECT COUNT(*) AS enriched_reviews FROM ZOMATO.AI.REVIEW_ENRICHED"
    )
    sentiment_breakdown = run_query(
        "SELECT sentiment_label, COUNT(*) AS count "
        "FROM ZOMATO.AI.REVIEW_ENRICHED "
        "GROUP BY sentiment_label ORDER BY count DESC"
    )
    topic_breakdown = run_query(
        "SELECT topic, COUNT(*) AS count "
        "FROM ZOMATO.AI.REVIEW_ENRICHED "
        "GROUP BY topic ORDER BY count DESC"
    )
    issues = run_query(
        "SELECT COALESCE(key_issue, 'Unknown') AS key_issue, COUNT(*) AS count "
        "FROM ZOMATO.AI.REVIEW_ENRICHED "
        "WHERE key_issue IS NOT NULL AND TRIM(key_issue) != '' "
        "GROUP BY key_issue ORDER BY count DESC LIMIT 10"
    )
    latest_reviews = run_query(
        "SELECT r.review_id, r.comment, e.sentiment_label, e.sentiment_score, "
        "e.topic, e.key_issue, e.enriched_at "
        "FROM ZOMATO.RAW.REVIEWS r "
        "JOIN ZOMATO.AI.REVIEW_ENRICHED e "
        "ON r.review_id = e.review_id "
        "ORDER BY e.enriched_at DESC LIMIT 50"
    )
    sentiment_trend = run_query(
        "SELECT DATE_TRUNC('day', enriched_at) AS day, sentiment_label, COUNT(*) AS count "
        "FROM ZOMATO.AI.REVIEW_ENRICHED "
        "GROUP BY day, sentiment_label ORDER BY day"
    )

    return {
        "counts": counts[0] if counts else {},
        "enriched_counts": enriched_counts[0] if enriched_counts else {},
        "sentiment_breakdown": sentiment_breakdown,
        "topic_breakdown": topic_breakdown,
        "issues": issues,
        "latest_reviews": latest_reviews,
        "sentiment_trend": sentiment_trend,
    }


def show_key_metrics(data: dict) -> None:
    total_reviews = data["counts"].get("total_reviews", 0)
    enriched_reviews = data["enriched_counts"].get("enriched_reviews", 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Raw Reviews", total_reviews)
    col2.metric("Enriched Reviews", enriched_reviews)
    col3.metric(
        "Enrichment Coverage",
        f"{round((enriched_reviews / total_reviews * 100), 1)}%" if total_reviews else "N/A",
    )


def render_breakdowns(data: dict) -> None:
    sentiment_df = pd.DataFrame(data["sentiment_breakdown"])
    topic_df = pd.DataFrame(data["topic_breakdown"])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sentiment Distribution")
        if not sentiment_df.empty:
            fig = px.pie(
                sentiment_df,
                names="sentiment_label",
                values="count",
                color="sentiment_label",
                color_discrete_map={
                    "positive": "#2ecc71",
                    "neutral": "#f1c40f",
                    "negative": "#e74c3c",
                },
                hole=0.35,
            )
            fig.update_layout(margin=dict(t=30, b=10, l=10, r=10), legend_title_text=None)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No sentiment data available yet.")

    with col2:
        st.subheader("Topic Distribution")
        if not topic_df.empty:
            fig = px.bar(
                topic_df,
                x="topic",
                y="count",
                color="topic",
                color_discrete_sequence=px.colors.qualitative.Safe,
                text="count",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_title=None, yaxis_title="Review Count", margin=dict(t=30, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No topic data available yet.")


def render_trends(data: dict) -> None:
    trend_df = pd.DataFrame(data["sentiment_trend"])
    if trend_df.empty:
        st.info("No trend data available yet.")
        return

    trend_df["day"] = pd.to_datetime(trend_df["day"]).dt.date
    fig = px.line(
        trend_df,
        x="day",
        y="count",
        color="sentiment_label",
        markers=True,
        color_discrete_map={
            "positive": "#2ecc71",
            "neutral": "#f1c40f",
            "negative": "#e74c3c",
        },
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Reviews", margin=dict(t=30, b=10, l=10, r=10))
    st.subheader("Sentiment Trend")
    st.plotly_chart(fig, use_container_width=True)


def render_issues(data: dict) -> None:
    issues_df = pd.DataFrame(data["issues"])
    st.subheader("Top Reported Issues")
    if not issues_df.empty:
        issues_df["rank"] = issues_df.index + 1
        st.dataframe(issues_df.rename(columns={"key_issue": "Issue", "count": "Count"}), use_container_width=True)
    else:
        st.write("No issue data available yet.")


def render_latest_reviews(data: dict, limit: int) -> None:
    latest_reviews_df = pd.DataFrame(data["latest_reviews"])
    st.subheader("Latest Enriched Reviews")
    if latest_reviews_df.empty:
        st.write("No enriched review rows available yet.")
        return

    latest_reviews_df["enriched_at"] = pd.to_datetime(latest_reviews_df["enriched_at"])
    latest_reviews_df = latest_reviews_df.head(limit)
    st.dataframe(
        latest_reviews_df.rename(
            columns={
                "review_id": "Review ID",
                "comment": "Comment",
                "sentiment_label": "Sentiment",
                "sentiment_score": "Score",
                "topic": "Topic",
                "key_issue": "Key Issue",
                "enriched_at": "Enriched At",
            }
        ),
        use_container_width=True,
    )


def main():
    st.set_page_config(
        page_title="Zomato Snowflake Dashboard",
        page_icon="🍽️",
        layout="wide",
    )

    st.title("Zomato Snowflake Review Dashboard")
    st.write(
        "This dashboard reads review and enrichment data directly from Snowflake using the configured Snowflake connection. "
        "Update env values in `ai/.env` or your environment before running."
    )

    with st.sidebar:
        st.header("Dashboard Controls")
        review_limit = st.slider("Latest review rows", 5, 50, 20)
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.experimental_rerun()

    try:
        data = load_dashboard_data()
    except Exception as exc:
        st.error(f"Failed to load data from Snowflake: {exc}")
        return

    show_key_metrics(data)
    st.markdown("---")
    render_breakdowns(data)
    st.markdown("---")
    render_trends(data)
    st.markdown("---")
    render_issues(data)
    st.markdown("---")
    render_latest_reviews(data, review_limit)


if __name__ == "__main__":
    main()
