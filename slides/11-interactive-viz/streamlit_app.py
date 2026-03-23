# NYC Flight Delay Explorer — Streamlit demo app
# Run with: streamlit run streamlit_app.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from nycflights13 import flights

# Page config
st.set_page_config(
    page_title="NYC Flight Delay Explorer",
    layout="wide",
)

# Data preparation (cached so it only runs once)
@st.cache_data
def load_data():
    weather = pd.read_csv("flights_weather.csv")
    flights_weather = pd.merge(
        flights, weather, how="left",
        on=["year", "month", "day", "hour", "origin"]
    )
    agg_cols = ["dep_delay", "arr_delay", "humid", "visib",
                "wind_speed", "precip", "pressure", "temp"]
    flights_weather_day = (
        flights_weather
        .groupby(["year", "month", "day", "origin"])
        .agg({col: "mean" for col in agg_cols})
        .reset_index()
    )
    monthly_delays = (
        flights_weather_day
        .groupby(["month", "origin"])[["dep_delay", "arr_delay"]]
        .mean()
        .reset_index()
    )
    return flights_weather_day, monthly_delays

flights_weather_day, monthly_delays = load_data()
fwd = flights_weather_day.dropna(subset=["humid", "dep_delay"])
origins = sorted(flights_weather_day["origin"].unique())

# Sidebar controls
st.sidebar.title("Controls")

selected_origins = st.sidebar.multiselect(
    "Origin airport(s)",
    options=origins,
    default=origins,
)

month_range = st.sidebar.slider(
    "Month range",
    min_value=1, max_value=12, value=(1, 12),
)

min_humid = st.sidebar.slider(
    "Minimum humidity (%)",
    min_value=0, max_value=100, value=0,
)

show_trendline = st.sidebar.checkbox("Show trendline", value=True)

# Main content
st.title("NYC Flight Delay Explorer")
st.markdown(
    "Explore how weather conditions relate to departure delays at "
    "EWR, JFK, and LGA in 2013."
)

if not selected_origins:
    st.warning("Please select at least one origin airport.")
    st.stop()

m_lo, m_hi = month_range

# Filter data
line_df = monthly_delays[
    monthly_delays["origin"].isin(selected_origins) &
    monthly_delays["month"].between(m_lo, m_hi)
]

scatter_df = fwd[
    fwd["origin"].isin(selected_origins) &
    fwd["month"].between(m_lo, m_hi) &
    (fwd["humid"] >= min_humid)
]

#  Plots (use Plotly but then call it in st)
col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly Departure Delay")
    fig_line = px.line(
        line_df, x="month", y="dep_delay", color="origin",
        markers=True,
        labels={"dep_delay": "Avg Dep Delay (min)", "month": "Month"},
        template="plotly_white",
    )
    fig_line.update_layout(legend_title_text="Origin")
    st.plotly_chart(fig_line, use_container_width=True)

with col2:
    st.subheader("Humidity vs. Departure Delay")
    fig_scatter = px.scatter(
        scatter_df, x="humid", y="dep_delay",
        color="origin", opacity=0.5,
        trendline="ols" if show_trendline else None,
        labels={"dep_delay": "Dep Delay (min)", "humid": "Humidity (%)"},
        template="plotly_white",
    )
    fig_scatter.update_layout(legend_title_text="Origin")
    st.plotly_chart(fig_scatter, use_container_width=True)

# Summary stats
st.subheader("Summary statistics")
summary = (
    scatter_df
    .groupby("origin")[["dep_delay", "arr_delay", "humid"]]
    .mean()
    .round(1)
    .rename(columns={
        "dep_delay": "Avg Dep Delay (min)",
        "arr_delay": "Avg Arr Delay (min)",
        "humid": "Avg Humidity (%)",
    })
)
st.dataframe(summary, use_container_width=True)
