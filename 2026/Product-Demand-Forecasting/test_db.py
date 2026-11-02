
import streamlit as st
import psycopg2

try:
    conn = psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        dbname=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )

    print("SUCCESS: Connected to PostgreSQL!")
    conn.close()

except Exception as e:
    print("Connection failed:", e)
