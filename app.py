import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="ClearBreathe — Family Asthma Safety",
    page_icon="🫁",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .score-green { background-color: #DEF7EC; border-left: 6px solid #0E9F6E; padding: 1.2rem; border-radius: 8px; color: #03543F; }
    .score-yellow { background-color: #FEF08A; border-left: 6px solid #CA8A04; padding: 1.2rem; border-radius: 8px; color: #713F12; }
    .score-red { background-color: #FDE8E8; border-left: 6px solid #E02424; padding: 1.2rem; border-radius: 8px; color: #9B1C1C; }
    .profile-card { background-color: #F3F4F6; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #E5E7EB; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA PERSISTENCE FOR USER ACCOUNTS
# ---------------------------------------------------------
USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ---------------------------------------------------------
# AUTHENTICATION & ONBOARDING SYSTEM
# ---------------------------------------------------------
if not st.session_state.current_user:
    st.title("🫁 Welcome to ClearBreathe")
    st.write("A personalized asthma trigger tracking and action platform for families.")

    tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Create Account"])

    with tab_login:
        st.subheader("Log in to your account")
        login_email = st.text_input("Parent Email / Username:", key="login_email")
        login_pass = st.text_input("Password:", type="password", key="login_pass")
        if st.button("Log In"):
            if login_email in st.session_state.users and st.session_state.users[login_email]["password"] == login_pass:
                st.session_state.current_user = login_email
                st.success("Log in successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab_signup:
        st.subheader("Parent Onboarding & Registration")
        st.write("Set up your account to save your child's profile and personalized Asthma Action Plan.")
        
        with st.form("signup_form"):
            email = st.text_input("Parent Email / Username")
            password = st.text_input("Create Password", type="password")
            
            st.divider()
            st.markdown("### 👧 Child Profile Details")
            child_name = st.text_input("Child's First Name", value="Alex")
            child_age = st.number_input("Child's Age", min_value=1, max_value=18, value=10)
            zip_code = st.text_input("Home Zip Code (for environmental data)", value="78641")

            st.divider()
            st.markdown("### 🩺 Child's Personalized Asthma Action Plan")
            green_plan = st.text_area("Green Zone Instructions (Doing Well)", value="Take Flovent 2 puffs morning & night. Use Albuterol before PE.")
            yellow_plan = st.text_area("Yellow Zone Instructions (Caution)", value="Coughing/wheezing: Continue Flovent, add Albuterol 2 puffs every 4 hours.")
            red_plan = st.text_area("Red Zone Instructions (Medical Alert)", value="Take Albuterol 4 puffs immediately. Call doctor or seek emergency care.")

            signup_submit = st.form_submit_button("Complete Setup & Create Account")
            if signup_submit:
                if email and password and email not in st.session_state.users:
                    st.session_state.users[email] = {
                        "password": password,
                        "child_name": child_name,
                        "child_age": child_age,
                        "zip_code": zip_code,
                        "green_plan": green_plan,
                        "yellow_plan": yellow_plan,
                        "red_plan": red_plan
                    }
                    save_users(st.session_state.users)
                    st.session_state.current_user = email
                    st.success("Account created successfully!")
                    st.rerun()
                elif email in st.session_state.users:
                    st.error("An account with this email already exists.")
                else:
                    st.error("Please fill out all required account fields.")
    st.stop()

# ---------------------------------------------------------
# LOGGED IN DASHBOARD
# ---------------------------------------------------------
user_data = st.session_state.users[st.session_state.current_user]

# CORE LOGIC: Unified Breathing Score Engine
def calculate_breathing_score(pm25_aqi, ozone_aqi, pollen_level, smoke_flag):
    max_aqi = max(pm25_aqi, ozone_aqi)
    if max_aqi >= 150 or pollen_level == "High" or smoke_flag:
        return "RED", "score-red", "🚨 High Air Hazard: Severe trigger warning across PM2.5/Pollen/Smoke. Follow Yellow/Red Action Plan steps."
    elif max_aqi >= 80 or pollen_level == "Moderate":
        return "YELLOW", "score-yellow", "⚠️ Moderate Trigger Warning: Consider pre-medicating before outdoor physical activity."
    else:
        return "GREEN", "score-green", "✅ Favorable Conditions: Low environmental asthma trigger risk detected."

# Sidebar Header & User Details
st.sidebar.title("🫁 ClearBreathe")
st.sidebar.markdown(f"**Parent Account:** {st.session_state.current_user}")
st.sidebar.markdown(f"**Child:** {user_data['child_name']} (Age {user_data['child_age']})")
st.sidebar.markdown(f"**Zip Code:** {user_data['zip_code']}")

if st.sidebar.button("🚪 Log Out"):
    st.session_state.current_user = None
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 🚨 Emergency Action")
col_e1, col_e2 = st.sidebar.columns(2)
with col_e1:
    if st.button("📞 Call Parent", use_container_width=True):
        st.sidebar.success("Dialing Primary Guardian...")
with col_e2:
    if st.button("🩺 Call Doctor", use_container_width=True):
        st.sidebar.info("Dialing Pediatrician...")

if st.sidebar.button("🚨 Call 911 / Find ER", type="primary", use_container_width=True):
    st.sidebar.error("Initiating 911 Emergency Protocol...")

st.sidebar.divider()

# Navigation
page = st.sidebar.radio("Navigation", ["Daily Breathing Score", "Outlook & Alerts", "Trigger Diary", "Asthma Action Plan"])

# PAGE 1: DAILY BREATHING SCORE
if page == "Daily Breathing Score":
    st.title(f"Today's Breathing Score for {user_data['child_name']}")
    st.caption("Consolidating pollen, ozone, PM2.5, and smoke data into a single actionable metric.")

    # Mock Environmental API Inputs
    pm25 = 45        
    ozone = 62       
    pollen = "Moderate" 
    smoke = False    

    score, css_class, summary = calculate_breathing_score(pm25, ozone, pollen, smoke)

    st.markdown(f"""
    <div class="{css_class}">
        <h2>Current Status: {score}</h2>
        <p style="font-size: 1.1rem; margin-bottom: 0;">{summary}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("Environmental Factors Breakdown")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(label="PM2.5 Particles", value=f"{pm25} AQI", delta="Moderate" if pm25 > 50 else "Good")
    m2.metric(label="Ozone Level", value=f"{ozone} AQI", delta="Caution" if ozone > 50 else "Good")
    m3.metric(label="Pollen (Cedar/Oak)", value=pollen, delta="Rising")
    m4.metric(label="Wildfire Smoke", value="Clear" if not smoke else "Detected")

    st.divider()

    st.subheader(f"🎒 Morning School Readiness Checklist ({user_data['child_name']})")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.checkbox("Rescue Inhaler (Albuterol) in backpack", value=True)
    with c2:
        st.checkbox("Spacer device attached", value=True)
    with c3:
        st.checkbox("Asthma Action Plan copy with school nurse", value=True)

# PAGE 2: OUTLOOK & ALERTS
elif page == "Outlook & Alerts":
    st.title("Tomorrow & Weekend Outlook")
    st.write(f"Plan outdoor activities and sports for {user_data['child_name']} around projected air quality triggers.")

    forecast_data = {
        "Day": ["Tomorrow (Friday)", "Saturday", "Sunday"],
        "Projected Score": ["YELLOW", "RED", "GREEN"],
        "Primary Trigger": ["Oak Pollen", "Wildfire Smoke + PM2.5", "Low Triggers"],
        "Recommendation": [
            "Pre-medicate before outdoor physical activity.",
            "Consider indoor birthday/soccer alternatives.",
            "Safe for extended outdoor play."
        ]
    }
    st.table(pd.DataFrame(forecast_data))

# PAGE 3: TRIGGER DIARY
elif page == "Trigger Diary":
    st.title("Symptom & Trigger Diary")
    st.write("Track daily symptoms to correlate personal triggers against regional pollen and air quality graphs.")

    with st.form("diary_form"):
        st.subheader("Log Today's Symptoms")
        symptom_score = st.slider("Daily Symptom Rating (0 = None, 3 = Severe):", 0, 3, 1)
        rescue_puffs = st.number_input("Rescue Inhaler Puffs Used Today:", min_value=0, max_value=20, value=1)
        notes = st.text_area("Notes:")
        
        submitted = st.form_submit_button("Log Entry")
        if submitted:
            st.success("Entry recorded in child's profile log.")

# PAGE 4: ASTHMA ACTION PLAN
elif page == "Asthma Action Plan":
    st.title(f"{user_data['child_name']}'s Asthma Action Plan")
    st.write("Direct instructions saved from your onboarding profile.")

    st.subheader("🟢 Green Zone: Doing Well")
    st.info(user_data["green_plan"])

    st.subheader("🟡 Yellow Zone: Caution / Symptoms Present")
    st.warning(user_data["yellow_plan"])

    st.subheader("🔴 Red Zone: Medical Alert / Severe Symptoms")
    st.error(user_data["red_plan"])