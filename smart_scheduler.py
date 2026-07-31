import pandas as pd
import numpy as np
import time
import json
from datetime import datetime
import os

LOG_FILE = "scheduler_log.csv"
USER_FILE = "users.json"
ACTIVE_USER_FILE = "active_user.json"

USER_PREFS = {
    "latest_hour": 21,  # don’t suggest after 9 PM
    "appliance_priority": {
        "Fridge": "essential",
        "Heater": "essential",
        "AC": "flexible",
        "Washing Machine": "flexible"
    }
}

# -----------------------
# Utility functions
# -----------------------

def get_active_user():
    """Get currently logged-in user email"""
    if not os.path.exists(ACTIVE_USER_FILE):
        return None
    with open(ACTIVE_USER_FILE, "r") as f:
        return json.load(f).get("email")

def get_user_appliances(email):
    """Get appliances registered for the user"""
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "r") as f:
        users = json.load(f)
    return users.get(email, {}).get("appliances", [])

def get_hourly_usage(csv_file="energy_log.csv"):
    email = get_active_user()
    if not email:
        print("❌ No active user found. Please log in via the web app first.")
        return pd.Series(dtype=float)

    appliances = get_user_appliances(email)
    if not appliances:
        print(f"⚠️ No appliances found for {email}")
        return pd.Series(dtype=float)

    df = pd.read_csv(csv_file, on_bad_lines="skip")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])
    df = df[df["Email"] == email]               # Filter user
    df = df[df["Appliance"].isin(appliances)]  # Filter user’s appliances
    if df.empty:
        return pd.Series(dtype=float)

    df["Hour"] = df["Timestamp"].dt.hour
    return df.groupby("Hour")["Usage_Watts"].mean()

def suggest_hours(hourly_avg, top_n=3):
    """Suggest the hours with lowest average usage before latest_hour"""
    valid = {h: u for h, u in hourly_avg.items() if h <= USER_PREFS["latest_hour"]}
    return sorted(valid, key=valid.get)[:top_n]

def save_schedule(suggestions):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([{"Timestamp": ts, "Suggested_Hours": suggestions}])
    header = not os.path.exists(LOG_FILE)
    df.to_csv(LOG_FILE, mode="a", header=header, index=False)

def convert_to_am_pm(hour):
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour if (1 <= hour <= 12) else (hour - 12 if hour > 12 else 12)
    return f"{hour12}:00 {suffix}"

# -----------------------
# Main function
# -----------------------

def smart_schedule():
    hourly_avg = get_hourly_usage()
    if hourly_avg.empty:
        print("⚠️ Not enough data to suggest hours.")
        return []

    suggestions = suggest_hours(hourly_avg, top_n=3)
    save_schedule(suggestions)
    return [convert_to_am_pm(h) for h in suggestions]

# -----------------------
# Run scheduler in loop
# -----------------------

if __name__ == "__main__":
    while True:
        hours = smart_schedule()
        if hours:
            print(f"Suggested hours to run the machines: {hours}")
        time.sleep(60)

