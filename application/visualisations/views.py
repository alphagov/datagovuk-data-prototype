import glob
import os

from flask import Blueprint, abort, current_app, render_template, url_for

from application.utils import load_data, load_json

visualisations_bp = Blueprint("visualisations", __name__, url_prefix="/visualisations")

_CASTS = {"int": int, "float": float, "str": str}


# if a cast fails then we can end up with gaps in
# series, but it's a best effort
def _safe_cast(cast, value):
    try:
        return cast(value)
    except (ValueError, TypeError):
        return None


def _list_visualisations():
    data_dir = os.path.join(current_app.config["PROJECT_ROOT"], "data")
    items = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        filename = os.path.basename(path)
        slug = os.path.splitext(filename)[0]
        config = load_json(filename)
        items.append({"slug": slug, "title": config["title"]})
    return items


@visualisations_bp.route("/")
def index():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Visualisations"},
    ]
    return render_template(
        "visualisations.html",
        breadcrumbs=breadcrumbs,
        visualisations=_list_visualisations(),
    )


@visualisations_bp.route("/<string:slug>")
def show(slug):
    try:
        config = load_json(f"{slug}.json")
    except FileNotFoundError:
        abort(404)

    data_config = config["data"]
    records = load_data(data_config["csv"])
    if data_config.get("reverse"):
        records.reverse()

    # data returned by csv readers are all strings
    # so we do a bit of casting. Could move the series
    # into the json but makes that a bit harder to read
    x_cast = _CASTS[data_config["x_type"]]
    x_col = data_config["x_col"]

    chart = config["chart"]
    for i, y in enumerate(data_config["y_cols"]):
        y_cast = _CASTS[y["type"]]
        chart["series"][i]["data"] = [
            [x_cast(r[x_col]), _safe_cast(y_cast, r[y["col"]])] for r in records
        ]

    return render_template(
        "chart.html",
        title=config["title"],
        chart_config=chart,
    )
