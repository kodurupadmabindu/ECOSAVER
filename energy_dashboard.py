
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import json
import os

# -------------------------------
# EMAIL CONFIG
# -------------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "karnatireddyrahul2005@gmail.com"      # change this
APP_PASSWORD = "vpbmnmqgnrndmsvk"          # change this (Google App Password)

USERS_FILE = "users.json"

# -------------------------------
# DASHBOARD FUNCTION
# -------------------------------
def run_dashboard():
    st.title("⚡ ECOSAVER — Smart Energy Dashboard")

    # -------------------------------
    # Load active user
    # -------------------------------
    if not os.path.exists("active_user.json"):
        st.warning("Please log in first.")
        return

    with open("active_user.json", "r") as f:
        active_user = json.load(f)

    user_email = active_user.get("email", None)
    if not user_email:
        st.warning("User not found in active session.")
        return

    st.sidebar.write(f"Logged in as: {user_email}")

    # -------------------------------
    # Load user details
    # -------------------------------
    if not os.path.exists(USERS_FILE):
        st.error("users.json not found.")
        return

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    user_info = users.get(user_email, {})
    appliances = user_info.get("appliances", [])

    st.sidebar.subheader("Your Appliances")
    if appliances:
        st.sidebar.write(", ".join(appliances))
    else:
        st.sidebar.write("No appliances selected.")

    # -------------------------------
    # Load energy data
    # -------------------------------
    data_file = "energy_log.csv"
    if not os.path.exists(data_file):
        st.error("energy_log.csv not found.")
        return

    df = pd.read_csv(data_file)

    # Ensure proper datatypes
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

    # Display data preview
    st.subheader("📊 Energy Usage Data")
    st.dataframe(df.tail())

    # -------------------------------
    # Appliance Filter
    # -------------------------------
    st.subheader("🧩 Select Appliance to View")
    selected_appliance = st.selectbox("Appliance", appliances if appliances else ["All"])

    if "Appliance" in df.columns and selected_appliance != "All":
        df = df[df["Appliance"] == selected_appliance]

    if df.empty:
        st.warning("No data found for this appliance.")
        return

    # -------------------------------
    # ML Prediction Logic
    # -------------------------------
    if "Usage" not in df.columns:
        st.error("CSV must contain a 'Usage' column.")
        return

    df = df.sort_values("Date")
    df["Day_Index"] = np.arange(len(df))

    # Train linear regression on past data
    model = LinearRegression()
    X = df[["Day_Index"]]
    y = df["Usage"]
    model.fit(X, y)

    # Predict the next day's usage
    next_day_index = np.array([[len(df)]])
    predicted_usage = model.predict(next_day_index)[0]
    st.info(f"🔮 Predicted next usage for {selected_appliance}: {predicted_usage:.2f} kWh")

    # -------------------------------
    # Compare Real vs Predicted
    # -------------------------------
    latest_usage = df["Usage"].iloc[-1]

    st.metric(label="Current Usage", value=f"{latest_usage:.2f} kWh")
    st.metric(label="Predicted Usage", value=f"{predicted_usage:.2f} kWh")

    if latest_usage > predicted_usage:
        st.error("⚠️ Real usage exceeded predicted usage! Sending alert email...")

        try:
            send_email_alert(user_email, selected_appliance, latest_usage, predicted_usage)
            st.success(f"📧 Alert email sent successfully to {user_email}")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
    else:
        st.success("✅ Usage is within predicted range.")

    # -------------------------------
    # Usage trend chart
    # -------------------------------
    st.subheader("📈 Energy Usage Trend")
    st.line_chart(df.set_index("Date")["Usage"])


# -------------------------------
# EMAIL ALERT FUNCTION
# -------------------------------
def send_email_alert(to_email, appliance, real_usage, predicted_usage):
    subject = f"⚠️ ECOSAVER Alert: High Usage in {appliance}"
    body = (
        f"Dear User,\n\n"
        f"Your {appliance}'s energy consumption ({real_usage:.2f} kWh) "
        f"has exceeded the predicted usage ({predicted_usage:.2f} kWh).\n\n"
        "Please check your appliance for any unusual activity.\n\n"
        "– ECOSAVER Smart Monitoring System"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())


# -------------------------------
# Run standalone
# -------------------------------
if __name__ == "__main__":
    run_dashboard()
  