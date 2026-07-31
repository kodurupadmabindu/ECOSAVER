import csv
import random
import time
import json
from datetime import datetime

CONFIG_FILE = "appliances.json"
USER_FILE = "users.json"
ACTIVE_USER_FILE = "active_user.json"
LOG_FILE = "energy_log.csv"
HEADER = ["Timestamp", "Email", "Appliance", "Usage_Watts"]

# Ensure header exists
try:
    with open(LOG_FILE, "x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
except FileExistsError:
    pass

def get_active_user():
    """Get the currently logged-in user's email."""
    try:
        with open(ACTIVE_USER_FILE, "r") as f:
            data = json.load(f)
            return data.get("email")
    except:
        return None

def load_user_appliances(email):
    """Load appliances for a specific user."""
    try:
        with open(USER_FILE, "r") as f:
            users = json.load(f)
            return users[email]["appliances"]
    except Exception as e:
        print(f"⚠️ Could not load appliances for {email}: {e}")
        return []

def get_usage():
    """Simulate appliance usage between 10 and 30 watts."""
    return random.randint(10, 30)

def log_entry(email, appliance, usage):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, email, appliance, usage])
    print(f"[{timestamp}] ({email}) {appliance} => {usage} W")

def realtime_logging(interval=60):
    """Log usage in real time for the active user."""
    email = get_active_user()
    if not email:
        print("❌ No active user found. Please log in via the web app first.")
        return

    appliances = load_user_appliances(email)
    if not appliances:
        print(f"⚠️ No appliances registered for {email}.")
        return

    print(f"📊 Starting real-time logging for {email} every {interval}s...")
    while True:
        for appliance in appliances:
            usage = get_usage()
            log_entry(email, appliance, usage)
        time.sleep(interval)

if __name__ == "__main__":
    realtime_logging(interval=60)
