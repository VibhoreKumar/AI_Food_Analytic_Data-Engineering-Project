import streamlit as st
import snowflake.connector
import pandas as pd

st.set_page_config(page_title="Zomato Analytics", layout="wide")

@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"],
    )

@st.cache_data(ttl=600)
def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)

st.title("🍽️ Zomato Analytics Dashboard")

df = run_query("SELECT * FROM ZOMATO.MARTS.DIM_RESTAURANTS LIMIT 10")
st.dataframe(df)