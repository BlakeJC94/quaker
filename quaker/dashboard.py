import json
import re

import dash_leaflet as dl
from dash import Dash, html, Input, Output

MAP_ID = "map-id"
COORDINATE_CLICK_ID = "coordinate-click-id"

DASHBOARD_DATA_LOCATION = "./scrap.csv"
# get with `quaker download > scrap.csv`
# TODO look into proper deployment with CherryPy


app = Dash(__name__)
app.title = "Quaker"
server = app.server

# app.config["suppress_callback_exceptions"] = True  # TODO once stable??

# Create layout.
app.layout = html.Div(
    [
        html.H1("Example: Gettings coordinates from click"),
        dl.Map(
            id=MAP_ID,
            style={"width": "1000px", "height": "500px"},
            center=[-37.813629, 144.963058],
            zoom=5,
            children=[dl.TileLayer()],
        ),
        html.P("Coordinate (click on map):"),
        html.Div(id=COORDINATE_CLICK_ID),
    ]
)

# TODO use dash leaflet to plot data
#   * Read foo.csv (download data beforehand)
#   * Plot points on map
#     * Colour by magnitude
#     * Automatically cluster (use biased mean for cluster color)

@app.callback(Output(COORDINATE_CLICK_ID, "children"), [Input(MAP_ID, "click_lat_lng")])
def click_coord(event):
    """Callback to read and output co-ordinates from click"""
    if event is None:
        return "---"
    output = json.dumps(event)
    lat, lon = (float(match) for match in re.findall(r"\d+\.?\d*", output)[:2])
    return f"[{lat}, {(float(lon) + 180) % 360 - 180}]"


def dashboard(
    host: str = "localhost",
    port: int = 8081,
):
    """Generate a visualisation dashboard for exploring earthquake events.

    Args:
        host: The hostname to serve the dashboard on, passed to Dash.
        port: The port to serve the dashboard on, passed to Dash.
    """
    app.run_server(host=host, port=port)
