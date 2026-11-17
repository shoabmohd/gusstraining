"""
SpaceX Launch Records Dashboard — IBM Plotly Dash lab
Run: pip install -r requirements.txt && python spacex_dash_app.py
Open: http://127.0.0.1:8050
"""
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "spacex_launch_dash.csv"
DATA_URL = (
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
    "IBM-DS0321EN-SkillsNetwork/datasets/spacex_launch_dash.csv"
)

def load_data():
    if not DATA_FILE.exists():
        try:
            pd.read_csv(DATA_URL).to_csv(DATA_FILE, index=False)
        except Exception as exc:
            raise FileNotFoundError(
                "Place spacex_launch_dash.csv beside this script. "
                "Automatic download from IBM's course endpoint failed."
            ) from exc

    df = pd.read_csv(DATA_FILE)
    required = ["Launch Site", "class", "Payload Mass (kg)",
                "Booster Version", "Booster Version Category"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing columns: {missing}")
    df["class"] = pd.to_numeric(df["class"], errors="coerce")
    df["Payload Mass (kg)"] = pd.to_numeric(df["Payload Mass (kg)"], errors="coerce")
    df = df.dropna(subset=["Launch Site", "class", "Payload Mass (kg)"]).copy()
    df["class"] = df["class"].astype(int)
    return df

spacex_df = load_data()
min_payload = max(0, int(spacex_df["Payload Mass (kg)"].min() // 1000 * 1000))
max_payload = max(10000, int(((spacex_df["Payload Mass (kg)"].max() + 999) // 1000) * 1000))
site_options = [{"label": "All Sites", "value": "ALL"}] + [
    {"label": site, "value": site}
    for site in sorted(spacex_df["Launch Site"].dropna().unique())
]

app = Dash(__name__)
app.title = "SpaceX Launch Records Dashboard"
app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "maxWidth": "1200px",
           "margin": "0 auto", "padding": "20px"},
    children=[
        html.H1("SpaceX Launch Records Dashboard",
                style={"textAlign": "center", "color": "#12304a"}),
        html.P("Explore launch outcomes by site, payload mass and booster.",
               style={"textAlign": "center"}),
        html.Label("Select a Launch Site:"),
        dcc.Dropdown(
            id="site-dropdown", options=site_options, value="ALL",
            placeholder="Select a Launch Site here", searchable=True,
            clearable=False
        ),
        dcc.Graph(id="success-pie-chart"),
        html.Hr(),
        html.Label("Select Payload Mass Range (kg):"),
        dcc.RangeSlider(
            id="payload-slider", min=0, max=max_payload, step=1000,
            marks={v: f"{v:,}" for v in range(0, max_payload + 1, 2000)},
            value=[min_payload, max_payload]
        ),
        dcc.Graph(id="success-payload-scatter-chart"),
        html.Footer("Source: IBM Skills Network SpaceX launch dashboard dataset",
                    style={"textAlign": "center", "fontSize": "12px"})
    ]
)

@app.callback(
    Output("success-pie-chart", "figure"),
    Input("site-dropdown", "value")
)
def get_pie_chart(entered_site):
    filtered = spacex_df if entered_site == "ALL" else spacex_df[
        spacex_df["Launch Site"] == entered_site
    ]
    # In this lab's class field, 1 is plotted as success and 0 as failure.
    outcome = filtered["class"].map({0: "Unsuccessful", 1: "Successful"})
    counts = outcome.value_counts().reindex(
        ["Successful", "Unsuccessful"], fill_value=0
    ).rename_axis("Launch Outcome").reset_index(name="Number of Launches")
    title = ("Launch Outcomes for All Sites" if entered_site == "ALL"
             else f"Launch Outcomes for {entered_site}")
    fig = px.pie(
        counts, values="Number of Launches", names="Launch Outcome",
        title=title, color="Launch Outcome",
        color_discrete_map={"Successful": "#2ca02c", "Unsuccessful": "#d62728"}
    )
    fig.update_traces(textposition="inside", textinfo="label+value+percent")
    return fig

@app.callback(
    Output("success-payload-scatter-chart", "figure"),
    [Input("site-dropdown", "value"), Input("payload-slider", "value")]
)
def get_scatter_chart(entered_site, payload_range):
    low, high = payload_range
    filtered = spacex_df[
        spacex_df["Payload Mass (kg)"].between(low, high)
    ]
    if entered_site != "ALL":
        filtered = filtered[filtered["Launch Site"] == entered_site]
    site_title = "All Launch Sites" if entered_site == "ALL" else entered_site
    fig = px.scatter(
        filtered, x="Payload Mass (kg)", y="class",
        color="Booster Version Category",
        hover_data=["Launch Site", "Booster Version"],
        title=f"Payload Mass vs. Launch Outcome — {site_title}",
        labels={"class": "Launch Outcome (0 = Failure, 1 = Success)"}
    )
    fig.update_yaxes(
        tickmode="array", tickvals=[0, 1],
        ticktext=["Unsuccessful (0)", "Successful (1)"]
    )
    return fig

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
