import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    config = {
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "ZOMATO"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
    }

    missing = [k for k in ["user", "password", "account"] if not config[k]]
    if missing:
        raise RuntimeError(
            f"Missing required Snowflake environment variables: {', '.join(missing)}. "
            "Check ai/.env or set them in your shell before running."
        )

    return snowflake.connector.connect(**config)


@st.cache_data(ttl=60)
def run_query(query: str) -> pd.DataFrame:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)
        df.columns = df.columns.str.lower()
        return df
    finally:
        cursor.close()
        conn.close()


def render_metrics(total: int, enriched: int) -> None:
    coverage = f"{round((enriched / total * 100), 1)}%" if total else "N/A"
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Raw Reviews", total, delta=None, delta_color="normal")
    col2.metric("Enriched Reviews", enriched, delta=None, delta_color="normal")
    col3.metric("Coverage", coverage, delta=None, delta_color="normal")


def render_sentiment_chart(sentiment: pd.DataFrame) -> None:
    st.subheader("Sentiment Distribution")
    if sentiment.empty:
        st.info("No sentiment data available yet.")
        return

    fig = px.pie(
        sentiment,
        names="sentiment_label",
        values="count",
        color="sentiment_label",
        color_discrete_map={"positive": "#2ecc71", "neutral": "#f1c40f", "negative": "#e74c3c"},
        hole=0.42,
        title="Review sentiment breakdown",
    )
    fig.update_traces(textinfo="percent+label", textfont_size=14)
    fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), legend_title_text=None)
    st.plotly_chart(fig, use_container_width=True)


def render_topic_chart(topic: pd.DataFrame) -> None:
    st.subheader("Topic Distribution")
    if topic.empty:
        st.info("No topic data available yet.")
        return

    fig = px.bar(
        topic,
        x="topic",
        y="count",
        color="topic",
        text="count",
        color_discrete_sequence=px.colors.qualitative.Vivid,
        title="Most discussed topics",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title=None, yaxis_title="Review count", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=40, l=0, r=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_trend_chart(trend: pd.DataFrame) -> None:
    st.subheader("Sentiment Trend")
    if trend.empty:
        st.info("No trend data available yet.")
        return

    trend["day"] = pd.to_datetime(trend["day"]).dt.date
    fig = px.line(
        trend,
        x="day",
        y="count",
        color="sentiment_label",
        markers=True,
        title="Daily sentiment volume",
        color_discrete_map={"positive": "#2ecc71", "neutral": "#f1c40f", "negative": "#e74c3c"},
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Review count", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=40, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)


def render_latest_reviews(latest: pd.DataFrame) -> None:
    st.subheader("Latest Enriched Reviews")
    if latest.empty:
        st.info("No enriched review rows available yet.")
        return

    latest["enriched_at"] = pd.to_datetime(latest["enriched_at"])
    latest_display = latest.rename(columns={
        "review_id": "Review ID",
        "comment": "Comment",
        "sentiment_label": "Sentiment",
        "sentiment_score": "Sentiment Score",
        "topic": "Topic",
        "key_issue": "Key Issue",
        "enriched_at": "Enriched At",
    })
    st.dataframe(latest_display, use_container_width=True)


def main():
    st.set_page_config(page_title="Food Delivery Analytic Dashboard", page_icon="🍽️", layout="wide")
    st.markdown(
        "<style>"
        "div.block-container{padding-top:1rem;}"
        "</style>",
        unsafe_allow_html=True,
    )

    st.title("Food Delivery Analytic Dashboard")
    st.write(
        "This dashboard visualizes AI-enriched customer review data, combining sentiment classification, topic extraction, and issue flagging to help identify patterns in customer feedback — such as which topics drive negative sentiment, and which issues appear most frequently across restaurants or cities."
    )

    with st.sidebar:
        st.header("Dashboard settings")
        row_limit = st.slider("Latest review rows", 5, 50, 20)
        st.markdown("---")
        st.caption("Make sure Snowflake credentials are configured in ai/.env before running.")
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.experimental_rerun()

    try:
        total_reviews = run_query("SELECT COUNT(*) AS total_reviews FROM ZOMATO.RAW.REVIEWS")
        enriched_reviews = run_query("SELECT COUNT(*) AS enriched_reviews FROM ZOMATO.AI.REVIEW_ENRICHED")
        sentiment = run_query(
            "SELECT sentiment_label, COUNT(*) AS count "
            "FROM ZOMATO.AI.REVIEW_ENRICHED "
            "GROUP BY sentiment_label ORDER BY count DESC"
        )
        topic = run_query(
            "SELECT topic, COUNT(*) AS count "
            "FROM ZOMATO.AI.REVIEW_ENRICHED "
            "GROUP BY topic ORDER BY count DESC"
        )
        trend = run_query(
            "SELECT DATE_TRUNC('day', enriched_at) AS day, sentiment_label, COUNT(*) AS count "
            "FROM ZOMATO.AI.REVIEW_ENRICHED "
            "GROUP BY day, sentiment_label ORDER BY day"
        )
        latest = run_query(
            f"SELECT r.review_id, r.comment, e.sentiment_label, e.sentiment_score, "
            f"e.topic, e.key_issue, e.enriched_at "
            f"FROM ZOMATO.RAW.REVIEWS r "
            f"JOIN ZOMATO.AI.REVIEW_ENRICHED e "
            f"ON r.review_id = e.review_id "
            f"ORDER BY e.enriched_at DESC LIMIT {row_limit}"
        )
    except Exception as error:
        st.error(f"Failed to load data from Snowflake: {error}")
        return

    total = int(total_reviews["total_reviews"].iloc[0])
    enriched = int(enriched_reviews["enriched_reviews"].iloc[0])

    render_metrics(total, enriched)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        render_sentiment_chart(sentiment)
    with col2:
        render_topic_chart(topic)

    st.markdown("---")
    render_trend_chart(trend)
    st.markdown("---")
    render_latest_reviews(latest)


if __name__ == "__main__":
    main()
