from flask import Flask, render_template, request, jsonify
from src.data_loader import load_all_data
from src.time_utils import assign_time_slots, SLOT_NAME_MAP, SLOT_ORDER
from src.analytics import get_summary_stats
from src.charts import generate_all_charts

app = Flask(__name__)

_orders_df, _dishes_df, _merged_df = load_all_data()
_merged_df = assign_time_slots(_merged_df)


@app.route("/")
def index():
    stats = get_summary_stats(_merged_df)
    charts = generate_all_charts(_merged_df)

    return render_template(
        "dashboard.html",
        stats=stats,
        initial_charts=charts,
        slot_name_map=SLOT_NAME_MAP,
    )


@app.route("/api/filter")
def filter_data():
    slot = request.args.get("slot", None)

    filtered_df = _merged_df
    if slot and slot in SLOT_ORDER:
        filtered_df = _merged_df[_merged_df["时段"] == slot]

    stats = get_summary_stats(filtered_df, slot_filter=slot)
    charts = generate_all_charts(_merged_df, selected_slot=slot)

    return jsonify(
        {
            "stats": stats,
            "charts": charts,
            "selected_slot": slot,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
