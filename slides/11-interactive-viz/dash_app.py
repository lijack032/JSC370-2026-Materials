# NYC Flight Delay Explorer — Dash demo app
# Run with: python dash_app.py
# Then open http://127.0.0.1:8050 in your browser

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from nycflights13 import flights

# ── Data preparation ──────────────────────────────────────────────────────────
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

fwd = flights_weather_day.dropna(subset=["humid", "dep_delay"])
origins = sorted(flights_weather_day["origin"].unique())

# ── App layout ────────────────────────────────────────────────────────────────
app = Dash(__name__)

app.layout = html.Div([

    html.H1("NYC Flight Delay Explorer",
            style={"fontFamily": "Arial, sans-serif", "textAlign": "center",
                   "color": "#2c3e50", "marginBottom": "5px"}),
    html.P("Explore how weather conditions relate to departure delays at NYC airports.",
           style={"textAlign": "center", "color": "#7f8c8d", "marginBottom": "25px",
                  "fontFamily": "Arial, sans-serif"}),

    # ── Controls row ──────────────────────────────────────────────────────────
    html.Div([

        html.Div([
            html.Label("Origin airport", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="origin-dd",
                options=[{"label": o, "value": o} for o in origins],
                value=origins,
                multi=True,
                clearable=False,
            ),
        ], style={"width": "30%", "display": "inline-block",
                  "verticalAlign": "top", "paddingRight": "30px"}),

        html.Div([
            html.Label("Month range", style={"fontWeight": "bold"}),
            dcc.RangeSlider(
                id="month-slider",
                min=1, max=12, step=1, value=[1, 12],
                marks={m: str(m) for m in range(1, 13)},
                tooltip={"placement": "bottom"},
            ),
        ], style={"width": "60%", "display": "inline-block",
                  "verticalAlign": "top"}),

    ], style={"padding": "0 40px 20px 40px", "fontFamily": "Arial, sans-serif"}),

    # ── Plots row ─────────────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(id="line-chart", style={"width": "50%", "display": "inline-block"}),
        dcc.Graph(id="scatter-chart", style={"width": "50%", "display": "inline-block"}),
    ]),

], style={"maxWidth": "1200px", "margin": "auto"})

# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("line-chart", "figure"),
    Output("scatter-chart", "figure"),
    Input("origin-dd", "value"),
    Input("month-slider", "value"),
)
def update(selected_origins, month_range):
    # Ensure selected_origins is always a list
    if isinstance(selected_origins, str):
        selected_origins = [selected_origins]

    m_lo, m_hi = month_range

    # Line chart — monthly mean dep_delay by origin
    line_df = monthly_delays[
        monthly_delays["origin"].isin(selected_origins) &
        monthly_delays["month"].between(m_lo, m_hi)
    ]
    line_fig = px.line(
        line_df, x="month", y="dep_delay", color="origin",
        markers=True,
        title="Mean Departure Delay by Month",
        labels={"dep_delay": "Avg Dep Delay (min)", "month": "Month"},
        template="plotly_white",
    )
    line_fig.update_layout(height=420, legend_title_text="Origin")

    # Scatter — humidity vs dep_delay
    scatter_df = fwd[
        fwd["origin"].isin(selected_origins) &
        fwd["month"].between(m_lo, m_hi)
    ]
    scatter_fig = px.scatter(
        scatter_df, x="humid", y="dep_delay",
        color="origin", opacity=0.5, trendline="ols",
        title="Humidity vs. Departure Delay",
        labels={"dep_delay": "Dep Delay (min)", "humid": "Humidity (%)"},
        template="plotly_white",
    )
    scatter_fig.update_layout(height=420, legend_title_text="Origin")

    return line_fig, scatter_fig


if __name__ == "__main__":
    app.run(debug=True)
