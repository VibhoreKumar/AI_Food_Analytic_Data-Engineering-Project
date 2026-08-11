# Food Delivery Analytics Dashboard querying Zomato review data from Snowflake
# Co-authored with CoCo
import os

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Food Delivery Analytic Dashboard", page_icon="\U0001f37d\ufe0f", layout="wide")

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))


@st.cache_data(ttl=60)
def run_query(query: str) -> pd.DataFrame:
    df = conn.query(query)
    df.columns = df.columns.str.lower()
    return df


def render_metrics(total: int, enriched: int) -> None:
    coverage = f"{round((enriched / total * 100), 1)}%" if total else "N/A"
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Raw Reviews", total)
    col2.metric("Enriched Reviews", enriched)
    col3.metric("Coverage", coverage)


def render_sentiment_chart(sentiment: pd.DataFrame) -> None:
    st.subheader("Sentiment Distribution")
    if sentiment.empty:
        st.info("No sentiment data available yet.")
        return

    color_map = alt.Scale(
        domain=["positive", "neutral", "negative"],
        range=["#2ecc71", "#f1c40f", "#e74c3c"],
    )
    chart = alt.Chart(sentiment).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("count:Q"),
        color=alt.Color("sentiment_label:N", scale=color_map, title="Sentiment"),
        tooltip=["sentiment_label", "count"],
    ).properties(height=300, title="Review sentiment breakdown")
    st.altair_chart(chart, use_container_width=True)


def render_topic_chart(topic: pd.DataFrame) -> None:
    st.subheader("Topic Distribution")
    if topic.empty:
        st.info("No topic data available yet.")
        return

    chart = alt.Chart(topic).mark_bar().encode(
        x=alt.X("topic:N", sort="-y", title=None),
        y=alt.Y("count:Q", title="Review count"),
        color=alt.Color("topic:N", legend=None),
        tooltip=["topic", "count"],
    ).properties(height=300, title="Most discussed topics")
    st.altair_chart(chart, use_container_width=True)


def render_trend_chart(trend: pd.DataFrame) -> None:
    st.subheader("Sentiment Trend")
    if trend.empty:
        st.info("No trend data available yet.")
        return

    trend["day"] = pd.to_datetime(trend["day"]).dt.date
    color_map = alt.Scale(
        domain=["positive", "neutral", "negative"],
        range=["#2ecc71", "#f1c40f", "#e74c3c"],
    )
    chart = alt.Chart(trend).mark_line(point=True).encode(
        x=alt.X("day:T", title="Date"),
        y=alt.Y("count:Q", title="Review count"),
        color=alt.Color("sentiment_label:N", scale=color_map, title="Sentiment"),
        tooltip=["day", "sentiment_label", "count"],
    ).properties(height=300, title="Daily sentiment volume")
    st.altair_chart(chart, use_container_width=True)


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
    st.title("Food Delivery Analytic Dashboard")
    st.write(
        "This dashboard visualizes AI-enriched customer review data, combining sentiment "
        "classification, topic extraction, and issue flagging to help identify patterns in "
        "customer feedback."
    )

    with st.sidebar:
        st.header("Dashboard settings")
        row_limit = st.slider("Latest review rows", 5, 50, 20)
        st.markdown("---")
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

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
