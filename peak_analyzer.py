import pandas as pd
import json
from statsmodels.tsa.arima.model import ARIMA

def get_active_user(active_user_file="active_user.json"):
    """Load currently active user's email."""
    try:
        with open(active_user_file, "r") as f:
            return json.load(f).get("email")
    except Exception:
        return None

def get_peak_prediction(csv_file="energy_log.csv", horizon=5, output="forecast.csv"):
    # Identify active user
    email = get_active_user()
    if not email:
        print("❌ No active user found. Please log in via the web app first.")
        return None

    # Load dataset
    try:
        df = pd.read_csv(csv_file, on_bad_lines="skip")
    except FileNotFoundError:
        print(f"⚠️ File not found: {csv_file}. Run logger.py first.")
        return None

    # Filter only this user's data
    df = df[df["Email"] == email]
    if df.empty:
        print(f"⚠️ No data found for {email}. Please run logger.py first.")
        return None

    # Convert timestamps
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])
    df["Hour"] = df["Timestamp"].dt.hour

    # Aggregate hourly average across all appliances
    hourly_avg = df.groupby("Hour")["Usage_Watts"].mean().reindex(range(24), fill_value=0)

    # Handle edge case: not enough variation for ARIMA
    if hourly_avg.nunique() <= 1:
        print("⚠️ Not enough data variation for ARIMA. Showing simple extrapolation.")
        results = []
        for i in range(horizon):
            hour = (hourly_avg.index[-1] + i + 1) % 24
            val = hourly_avg.mean()
            results.append({
                "Hour": hour,
                "Predicted_Usage": round(float(val), 2),
                "Lower_CI": round(float(val * 0.9), 2),
                "Upper_CI": round(float(val * 1.1), 2)
            })
        out_df = pd.DataFrame(results)
        out_df.to_csv(output, index=False)
        print(out_df.to_string(index=False))
        return out_df

    # Fit ARIMA model
    try:
        model = ARIMA(hourly_avg.values, order=(2, 1, 2))
        fitted = model.fit()
    except Exception as e:
        print(f"⚠️ ARIMA model failed: {e}")
        return None

    # Forecast next hours
    forecast = fitted.get_forecast(steps=horizon)
    pred_mean = forecast.predicted_mean
    conf_int = forecast.conf_int(alpha=0.2)

    # Prepare forecast results
    results = []
    for i in range(horizon):
        hour = (hourly_avg.index[-1] + i + 1) % 24
        mean = pred_mean[i]
        low, high = conf_int.iloc[i]
        results.append({
            "Hour": hour,
            "Predicted_Usage": max(0, round(float(mean), 2)),
            "Lower_CI": max(0, round(float(low), 2)),
            "Upper_CI": max(0, round(float(high), 2))
        })

    # Save to CSV
    out_df = pd.DataFrame(results)
    out_df.to_csv(output, index=False)

    print(f"\n📊 Forecast for next {horizon} hours ({email}):")
    print(out_df.to_string(index=False))
    print(f"\n✅ Forecast saved to {output}")

    return out_df

if __name__ == "__main__":
    get_peak_prediction()
