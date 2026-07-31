import streamlit as st
import json
import os
import energy_dashboard
from db_connection import get_database

st.write("ECOSAVER is running")
# -------------------------------
# CONFIGURATION
# -------------------------------
USER_FILE = "users.json"
ACTIVE_USER_FILE = "active_user.json"

st.set_page_config(page_title="ECOSAVER", layout="wide")

# -------------------------------
# USER MANAGEMENT HELPERS
# -------------------------------
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def set_active_user(email):
    with open(ACTIVE_USER_FILE, "w") as f:
        json.dump({"email": email}, f)

def clear_active_user():
    if os.path.exists(ACTIVE_USER_FILE):
        os.remove(ACTIVE_USER_FILE)

# -------------------------------
# MAIN LOGIN / REGISTER UI
# -------------------------------
st.title("🔋 ECOSAVER — Smart Energy Login")

users = load_users()

tab1, tab2 = st.tabs(["🔑 Login", "🆕 Register"])

# -------------------------------
# LOGIN TAB
# -------------------------------
with tab1:
    email = st.text_input("📧 Email")
    meter = st.text_input("🔢 Meter Number")

    if st.button("Login"):
        if email in users and users[email]["meter"] == meter:
            st.session_state["user"] = {"email": email}
            set_active_user(email)
            st.success("✅ Login successful! Redirecting to your dashboard...")
            st.rerun()
        else:
            st.error("❌ Invalid email or meter number.")

# -------------------------------
# REGISTER TAB
# -------------------------------
with tab2:
    name = st.text_input("👤 Name", key="reg_name")
    reg_email = st.text_input("📧 Email", key="reg_email")
    reg_meter = st.text_input("🔢 Meter Number", key="reg_meter")
    appliances = st.multiselect("⚙️ Select Your Appliances", ["AC", "Refrigerator", "Washing Machine", "TV"])

    if st.button("Register"):
        if reg_email in users:
            st.warning("⚠️ User already exists. Please log in.")
        else:
            users[reg_email] = {
                "name": name,
                "meter": reg_meter,
                "appliances": appliances
            }
            save_users(users)
            st.success("✅ Registration successful! Please log in.")

# -------------------------------
# AUTO-REDIRECT TO DASHBOARD IF LOGGED IN
# -------------------------------
if os.path.exists(ACTIVE_USER_FILE):
    with open(ACTIVE_USER_FILE, "r") as f:
        user_email = json.load(f).get("email")

    if user_email:
        st.session_state["user"] = {"email": user_email}
        st.sidebar.success(f"Logged in as: {user_email}")

        if st.sidebar.button("🔓 Logout"):
            clear_active_user()
            st.session_state.pop("user", None)
            st.success("You have been logged out.")
            st.rerun()

        # Run the Energy Dashboard
        energy_dashboard.run_dashboard()


# Get DB and collection
db = get_database()
users_collection = db["users"]   # collection for registration

st.title("User Registration Form 📝")

name = st.text_input("Enter Name")
email = st.text_input("Enter Email")
password = st.text_input("Enter Password", type="password")

if st.button("Register"):
    if name and email and password:
        # Check if user already exists
        if users_collection.find_one({"email": email}):
            st.error("User with this email already exists.")
        else:
            users_collection.insert_one({
                "name": name,
                "email": email,
                "password": password
            })
            st.success("✅ Registration successful!")
    else:
        st.warning("Please fill all fields.")

# Display All Users
st.subheader("Registered Users:")
for user in users_collection.find({}, {"_id": 0}):  # hide _id
    st.write(user)
