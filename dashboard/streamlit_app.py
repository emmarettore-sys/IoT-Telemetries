import os

import httpx
import pandas as pd
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="IoT Telemetry", page_icon="📡", layout="wide")
st.title("📡 IoT Telemetry Dashboard")

if st.button("Aggiorna dati"):
    st.rerun()

try:
    response = httpx.get(f"{API_URL}/api/telemetry/latest", timeout=5)
    response.raise_for_status()
    data = response.json()
except httpx.HTTPError as error:
    st.error(f"API non raggiungibile: {error}")
    st.stop()

if not data:
    st.info("Nessun dato disponibile. Avvia il simulatore per iniziare.")
    st.stop()

df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

col1, col2, col3 = st.columns(3)
col1.metric("Temperatura media", f"{df['temperature'].mean():.1f} °C")
col2.metric("Umidità media", f"{df['humidity'].mean():.1f} %")
col3.metric("Pressione media", f"{df['pressure'].mean():.1f} hPa")

st.subheader("Telemetria recente")
st.line_chart(df.set_index("timestamp")[["temperature", "humidity", "pressure"]])
st.dataframe(df, use_container_width=True, hide_index=True)
