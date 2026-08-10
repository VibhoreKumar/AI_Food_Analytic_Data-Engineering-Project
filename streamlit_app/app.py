import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zomato Analytics", layout="wide")

@st.cache_resource
def get_connection():
    conn = snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"],
    )
    print("Snowflake connection established", flush=True)
    return conn

@st.cache_data(ttl=3600)
def run_query(query):
    conn = get_connection()
    print(f"▶️ Running query: {query}", flush=True)
    df = pd.read_sql(query, conn)
    print(f" Query returned {len(df)} rows", flush=True)
    return df

st.title("🍽️ Food-Delivery Analytics Dashboard")

# --- Step 4: manual refresh button ---
if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()

# --- Load base data for filters ---
restaurants_df = run_query("SELECT * FROM ZOMATO.MARTS.DIM_RESTAURANTS")

# --- Step 1: sidebar filters ---
st.sidebar.header("Filters")
city_options = sorted(restaurants_df["CITY"].dropna().unique())
selected_cities = st.sidebar.multiselect("City", options=city_options)

filtered_restaurants = restaurants_df[restaurants_df["CITY"].isin(selected_cities)]# --- Load remaining marts ---
orders_df = run_query("SELECT * FROM ZOMATO.MARTS.FCT_ORDERS")
city_revenue_df = run_query("SELECT * FROM ZOMATO.MARTS.MART_DAILY_CITY_REVENUNE")
delivery_sla_df = run_query("SELECT * FROM ZOMATO.MARTS.MART_DELIVERY_SLA")
restaurant_perf_df = run_query("SELECT * FROM ZOMATO.MARTS.MART_RESTAURANT_PERFORMANCE")
review_insights_df = run_query("SELECT * FROM ZOMATO.MARTS.MART_REVIEW_INSIGHTS")

# Apply city filter across relevant tables
city_revenue_filtered = city_revenue_df[city_revenue_df["CITY"].isin(selected_cities)].sort_values("ORDER_DATE")
delivery_sla_filtered = delivery_sla_df[delivery_sla_df["CITY"].isin(selected_cities)] if "CITY" in delivery_sla_df.columns else delivery_sla_df
review_insights_filtered = review_insights_df[review_insights_df["CITY"].isin(selected_cities)]

# --- Top-level metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Restaurants", len(filtered_restaurants))
col2.metric("Total Orders", f"{len(orders_df):,}")
avg_rating = pd.to_numeric(filtered_restaurants['RATING'], errors='coerce').mean()
col3.metric("Avg Rating", f"{avg_rating:.1f} ⭐" if pd.notna(avg_rating) else "N/A")
total_revenue = pd.to_numeric(orders_df['SALES_AMOUNT'], errors='coerce').sum()
col4.metric("Total Revenue", f"₹{total_revenue:,.0f}")

st.divider()

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📈 Revenue", "🚚 Delivery SLA", "🏆 Restaurant Performance", "💬 Review Sentiment"])

with tab1:
    st.subheader("Daily Revenue by City")
    fig = px.bar(city_revenue_filtered.sort_values("ORDER_DATE"), x="ORDER_DATE", y="GMV", color="CITY")
    st.plotly_chart(fig, use_container_width=True)

    fig_aov = px.line(city_revenue_filtered, x="ORDER_DATE", y="AOV", color="CITY", title="Average Order Value")
    st.plotly_chart(fig_aov, use_container_width=True)

    st.dataframe(city_revenue_filtered)

with tab2:
    st.subheader("Delivery SLA Overview")
    st.dataframe(delivery_sla_filtered)

with tab3:
    st.subheader("Top Performing Restaurants")
    st.dataframe(restaurant_perf_df)

with tab4:
    st.subheader("Review Sentiment by City & Topic")
    fig2 = px.bar(review_insights_filtered, x="TOPIC", y="REVIEWS", color="SENTIMENT_LABEL", barmode="group")
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(review_insights_filtered)