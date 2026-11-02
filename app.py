from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import uuid

app = Flask(__name__)
app.secret_key = "weather-project-demo-key"

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
CHART_DIR = BASE_DIR / "static" / "charts"
UPLOAD_DIR.mkdir(exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED = ["record_id", "observation_date", "location",
            "temperature", "humidity", "rainfall"]

SAMPLE_FILE = BASE_DIR / "weather.csv"
CURRENT_FILE = UPLOAD_DIR / "current_weather.csv"


def read_and_validate(file_path):
    """Read the CSV, report missing/invalid fields, and return valid rows."""
    raw = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    missing_columns = [c for c in REQUIRED if c not in raw.columns]
    if missing_columns:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing_columns))

    raw = raw[REQUIRED].copy()
    total_rows = len(raw)
    report = {}

    # Empty cells are counted as missing; non-empty values that cannot be parsed are invalid.
    date_text = raw["observation_date"].str.strip()
    date_missing = date_text.eq("")
    dates = pd.to_datetime(date_text, errors="coerce")
    date_invalid = (~date_missing) & dates.isna()
    report["observation_date"] = {
        "missing": int(date_missing.sum()), "invalid": int(date_invalid.sum())
    }

    location_text = raw["location"].str.strip()
    location_missing = location_text.eq("")
    report["location"] = {"missing": int(location_missing.sum()), "invalid": 0}

    numeric = {}
    for col in ["temperature", "humidity", "rainfall"]:
        text = raw[col].str.strip()
        missing = text.eq("")
        values = pd.to_numeric(text, errors="coerce")
        invalid = (~missing) & values.isna()
        if col == "humidity":
            invalid |= values.notna() & ~values.between(0, 100)
        elif col == "rainfall":
            invalid |= values.notna() & (values < 0)
        elif col == "temperature":
            invalid |= values.notna() & ~values.between(-90, 60)
        report[col] = {"missing": int(missing.sum()), "invalid": int(invalid.sum())}
        numeric[col] = values

    id_text = raw["record_id"].str.strip()
    id_missing = id_text.eq("")
    report["record_id"] = {"missing": int(id_missing.sum()), "invalid": 0}

    valid_mask = ~(date_missing | date_invalid | location_missing | id_missing)
    for col in numeric:
        txt = raw[col].str.strip()
        missing = txt.eq("")
        values = numeric[col]
        bad = (~missing) & values.isna()
        if col == "humidity":
            bad |= values.notna() & ~values.between(0, 100)
        elif col == "rainfall":
            bad |= values.notna() & (values < 0)
        elif col == "temperature":
            bad |= values.notna() & ~values.between(-90, 60)
        valid_mask &= ~(missing | bad)

    clean = raw.loc[valid_mask].copy()
    clean["observation_date"] = dates.loc[valid_mask]
    for col, values in numeric.items():
        clean[col] = values.loc[valid_mask]
    clean["location"] = clean["location"].str.strip()
    clean["record_id"] = clean["record_id"].str.strip()

    # Duplicate rows are removed and counted separately.
    before_duplicates = len(clean)
    clean = clean.drop_duplicates()
    duplicate_rows = before_duplicates - len(clean)

    report["total_rows"] = total_rows
    report["valid_rows"] = len(clean)
    report["excluded_rows"] = total_rows - len(clean)
    report["duplicate_rows"] = duplicate_rows
    return clean.sort_values("observation_date"), report


def make_charts(df):
    for old in CHART_DIR.glob("*.png"):
        old.unlink()

    if df.empty:
        return {}

    city = request.args.get("city", "All")
    view = df if city == "All" else df[df["location"] == city]
    if view.empty:
        return {}

    monthly = (view.assign(month=view["observation_date"].dt.to_period("M").astype(str))
               .groupby("month", as_index=False)
               .agg(avg_temp=("temperature", "mean"),
                    total_rain=("rainfall", "sum"),
                    avg_humidity=("humidity", "mean")))

    suffix = uuid.uuid4().hex[:8]
    paths = {}

    fig, ax = plt.subplots(figsize=(9, 4))
    for location, part in view.groupby("location"):
        daily = part.groupby("observation_date")["temperature"].mean()
        ax.plot(daily.index, daily.values, marker="o", label=location)
    ax.set_title(f"Temperature trend — {city}")
    ax.set_xlabel("Observation date")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(alpha=.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    name = f"temperature_{suffix}.png"
    fig.savefig(CHART_DIR / name, dpi=130)
    plt.close(fig)
    paths["temperature"] = name

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(monthly["month"], monthly["total_rain"], color="#4b91d1")
    ax.set_title(f"Monthly rainfall — {city}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total rainfall (mm)")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    name = f"rainfall_{suffix}.png"
    fig.savefig(CHART_DIR / name, dpi=130)
    plt.close(fig)
    paths["rainfall"] = name

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(monthly["month"], monthly["avg_temp"], marker="o",
            color="#e47739", label="Average temperature (°C)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average temperature (°C)")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(alpha=.25)
    ax2 = ax.twinx()
    ax2.bar(monthly["month"], monthly["total_rain"], alpha=.22,
            color="#367fc0", label="Total rainfall (mm)")
    ax2.set_ylabel("Total rainfall (mm)")
    ax.set_title(f"Monthly temperature and rainfall comparison — {city}")
    lines, labels = ax.get_legend_handles_labels()
    bars, bar_labels = ax2.get_legend_handles_labels()
    ax.legend(lines + bars, labels + bar_labels, loc="upper left")
    fig.tight_layout()
    name = f"comparison_{suffix}.png"
    fig.savefig(CHART_DIR / name, dpi=130)
    plt.close(fig)
    paths["comparison"] = name
    return paths


@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        uploaded = request.files.get("weather_file")
        if not uploaded or uploaded.filename == "":
            flash("Please choose a CSV file.")
            return redirect(url_for("dashboard"))
        if Path(uploaded.filename).suffix.lower() != ".csv":
            flash("Only CSV files are accepted.")
            return redirect(url_for("dashboard"))
        uploaded.save(CURRENT_FILE)
        try:
            checked, _ = read_and_validate(CURRENT_FILE)
            if checked.empty:
                flash("The file was uploaded, but it contains no valid records. Check the data quality report.")
            else:
                flash("CSV uploaded successfully. The dashboard has been updated.")
        except Exception as exc:
            CURRENT_FILE.unlink(missing_ok=True)
            flash(str(exc))
        return redirect(url_for("dashboard"))

    data_file = CURRENT_FILE if CURRENT_FILE.exists() else SAMPLE_FILE
    try:
        df, quality = read_and_validate(data_file)
    except Exception as exc:
        return f"Could not read weather data: {exc}", 400

    cities = sorted(df["location"].unique().tolist())
    selected_city = request.args.get("city", "All")
    view = df if selected_city == "All" else df[df["location"] == selected_city]
    if selected_city != "All" and selected_city not in cities:
        selected_city = "All"
        view = df

    daily = (view.groupby(view["observation_date"].dt.strftime("%Y-%m-%d"), as_index=False)
             .agg(min_temp=("temperature", "min"),
                  max_temp=("temperature", "max"),
                  avg_temp=("temperature", "mean"),
                  min_humidity=("humidity", "min"),
                  max_humidity=("humidity", "max"),
                  avg_humidity=("humidity", "mean"),
                  total_rain=("rainfall", "sum"))
             .rename(columns={"observation_date": "date"})
             .sort_values("date", ascending=False).head(15))

    monthly = (view.assign(month=view["observation_date"].dt.to_period("M").astype(str))
               .groupby("month", as_index=False)
               .agg(min_temp=("temperature", "min"),
                    max_temp=("temperature", "max"),
                    avg_temp=("temperature", "mean"),
                    min_humidity=("humidity", "min"),
                    max_humidity=("humidity", "max"),
                    avg_humidity=("humidity", "mean"),
                    total_rain=("rainfall", "sum")))

    charts = make_charts(df)
    return render_template(
        "index.html", cities=cities, selected_city=selected_city,
        records=len(view),
        avg_temp=round(float(np.mean(view["temperature"])), 1) if not view.empty else 0,
        avg_humidity=round(float(np.mean(view["humidity"])), 1) if not view.empty else 0,
        total_rain=round(float(np.sum(view["rainfall"])), 1) if not view.empty else 0,
        daily=daily.to_dict("records"),
        monthly=monthly.round(1).to_dict("records"),
        quality=quality, charts=charts,
        data_name=data_file.name,
        has_data=not view.empty
    )


if __name__ == "__main__":
    app.run(debug=True)
