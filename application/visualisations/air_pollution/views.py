import json

from flask import Blueprint, render_template

from application.utils import load_data

air_pollution = Blueprint("air_pollution", __name__, template_folder="templates")


@air_pollution.route("/air-pollution")
def index():
    records = load_data("fig17_urban_days_above_moderate.csv")

    # CSV is in reverse chronological order, most recent first, reverse to get oldest first
    records.reverse()

    series_data = [
        [
            int(r["Year"]),
            float(r["Mean number of days with moderate or above pollution"]),
        ]
        for r in records
    ]

    return render_template(
        "air-pollution.html",
        series_data=json.dumps(series_data),
    )
