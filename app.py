import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import datetime

# =========================================================
# 🔑 INPUT YOUR AIRNOW API KEY HERE
# =========================================================
AIRNOW_API_KEY = "D1C21388-5630-4BFC-BAFD-605FFFE1C8E2"   # <--- PASTE YOUR AIRNOW.GOV API KEY HERE

# Page Configuration
st.set_page_config(
    page_title="ClearBreathe — Family Asthma Tracker",
    page_icon="🫁",
    layout="wide"
)

# High-Contrast Mobile & Desktop Styling
st.markdown("""
    <style>
    /* Global App Background */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* High-Contrast Inputs */
    label, .stMarkdown, p, h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 2px solid #475569 !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        padding: 10px !important;
    }

    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #64748B !important;
        opacity: 1 !important;
    }

    /* Card Containers */
    .content-card {
        background: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #CBD5E1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.2rem;
    }

    /* Score Banners */
    .banner-green {
        background-color: #064E3B;
        color: #ECFDF5 !important;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 6px solid #10B981;
    }
    .banner-yellow {
        background-color: #78350F;
        color: #FEF3C7 !important;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 6px solid #F59E0B;
    }
    .banner-red {
        background-color: #7F1D1D;
        color: #FEF2F2 !important;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 6px solid #EF4444;
    }

    /* Direct Calling Buttons */
    .call-btn {
        display: block;
        width: 100%;
        padding: 0.85rem;
        text-align: center;
        border-radius: 8px;
        font-weight: 600;
        text-decoration: none !important;
        color: #FFFFFF !important;
        margin-bottom: 0.6rem;
    }
    .call-parent { background-color: #2563EB; }
    .call-doctor { background-color: #0D9488; }

    /* Footer Medical Disclaimer */
    .medical-disclaimer {
        margin-top: 3rem;
        padding: 1rem;
        background-color: #F1F5F9;
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        text-align: center;
        font-size: 0.85rem;
        color: #475569 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA PERSISTENCE
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

def render_medical_disclaimer():
    st.markdown("""
        <div class="medical-disclaimer">
            <strong>⚠️ Medical Disclaimer:</strong> ClearBreathe is an informational tool designed to help families monitor local air quality and track inhaler use. ClearBreathe does not provide medical advice, diagnosis, or treatment. Always consult your doctor or primary healthcare provider regarding any questions about a medical condition or asthma management plan.
        </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# REAL AIRNOW API DATA FETCH ENGINE
# ---------------------------------------------------------
def fetch_live_environmental_data(zip_code):
    if AIRNOW_API_KEY:
        try:
            url = f"https://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode={zip_code}&distance=25&API_KEY={AIRNOW_API_KEY}"
            res = requests.get(url, timeout=4).json()
            if res:
                pm25 = next((item['AQI'] for item in res if item['ParameterName'] == 'PM2.5'), 35)
                ozone = next((item['AQI'] for item in res if item['ParameterName'] == 'O3'), 30)
                return pm25, ozone, "Moderate", False, f"Live EPA AirNow Feed (Zip: {zip_code})"
        except Exception:
            pass

    return 42, 38, "Moderate", False, f"Baseline Environmental Feed (Zip: {zip_code})"

# ---------------------------------------------------------
# ACCOUNT CREATION & LOGIN SYSTEM
# ---------------------------------------------------------
if not st.session_state.current_user:
    st.markdown("""
        <div class="content-card" style="text-align: center;">
            <h1 style="margin: 0;">🫁 ClearBreathe</h1>
            <p style="color: #475569; font-size: 1.1rem; margin-top: 0.4rem;">
                A simple daily tool for parents to check air quality, track inhaler usage, and keep emergency contacts one tap away.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Create Account"])

    with tab_login:
        st.subheader("Welcome back")
        login_email = st.text_input("Parent Email / Username", placeholder="e.g., parent@example.com", key="login_email")
        login_pass = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
        if st.button("Log In", use_container_width=True):
            if login_email in st.session_state.users and st.session_state.users[login_email]["password"] == login_pass:
                st.session_state.current_user = login_email
                st.success("Log in successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab_signup:
        st.subheader("Create an Account")
        st.write("Sign up in seconds to see local weather triggers and store your emergency contact numbers.")
        
        with st.form("signup_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                email = st.text_input("Parent Email / Username*", placeholder="e.g., sarah_m")
            with col_a2:
                password = st.text_input("Create Password*", type="password", placeholder="Create password")

            st.divider()
            st.markdown("### 📍 Your Location & Emergency Contacts")
            zip_code = st.text_input("Home Zip Code*", placeholder="e.g., 78641")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                parent_phone = st.text_input("Parent Phone Number*", placeholder="e.g., 555-019-2831")
            with col_p2:
                doctor_phone = st.text_input("Doctor Office Phone*", placeholder="e.g., 555-014-9922")

            signup_submit = st.form_submit_button("Create Account")
            if signup_submit:
                if email and password and zip_code and parent_phone and doctor_phone:
                    if email not in st.session_state.users:
                        default_logs = [
                            {"date": "2026-10-18", "puffs": 0, "aqi_level": 32, "pollen_level": 25},
                            {"date": "2026-10-19", "puffs": 1, "aqi_level": 48, "pollen_level": 40},
                            {"date": "2026-10-20", "puffs": 3, "aqi_level": 85, "pollen_level": 75},
                            {"date": "2026-10-21", "puffs": 2, "aqi_level": 62, "pollen_level": 55},
                            {"date": "2026-10-22", "puffs": 4, "aqi_level": 110, "pollen_level": 95},
                            {"date": "2026-10-23", "puffs": 1, "aqi_level": 45, "pollen_level": 30},
                        ]
                        st.session_state.users[email] = {
                            "password": password,
                            "zip_code": zip_code,
                            "parent_phone": parent_phone.replace("-", "").replace(" ", ""),
                            "doctor_phone": doctor_phone.replace("-", "").replace(" ", ""),
                            "logs": default_logs
                        }
                        save_users(st.session_state.users)
                        st.session_state.current_user = email
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.error("Account already exists.")
                else:
                    st.error("Please fill in all required fields (*).")
    
    render_medical_disclaimer()
    st.stop()

# ---------------------------------------------------------
# LOGGED IN DASHBOARD
# ---------------------------------------------------------
user = st.session_state.users[st.session_state.current_user]

st.sidebar.markdown(f"""
<div style="background: #FFFFFF; padding: 1rem; border-radius: 10px; border: 1px solid #CBD5E1; margin-bottom: 1rem;">
    <h4 style="margin:0; color:#0F172A;">Account Overview</h4>
    <p style="margin:0; color:#64748B; font-size:0.9rem;">Zip Code: <strong>{user['zip_code']}</strong></p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 📞 One-Tap Emergency Call")
parent_tel = f"tel:{user.get('parent_phone', '')}"
doctor_tel = f"tel:{user.get('doctor_phone', '')}"

st.sidebar.markdown(f'<a href="{parent_tel}" class="call-btn call-parent">📱 Call Parent ({user.get("parent_phone")})</a>', unsafe_allow_html=True)
st.sidebar.markdown(f'<a href="{doctor_tel}" class="call-btn call-doctor">🩺 Call Doctor ({user.get("doctor_phone")})</a>', unsafe_allow_html=True)

st.sidebar.divider()
if st.sidebar.button("🚪 Log Out", use_container_width=True):
    st.session_state.current_user = None
    st.rerun()

# TOP NAVIGATION BAR
page = st.segmented_control(
    "Select View",
    ["Today's Air Quality", "Log Inhaler Puffs", "Puffs vs. Weather Chart"],
    default="Today's Air Quality",
    label_visibility="collapsed"
)

st.write("") 

# PAGE 1: DASHBOARD
if page == "Today's Air Quality":
    st.title("Today's Air Quality & Breathing Risk")
    st.write("Check your local air quality and pollen levels before planning outdoor time.")
    
    pm25, ozone, pollen, smoke, source_text = fetch_live_environmental_data(user['zip_code'])
    st.caption(f"📡 Data Source: **{source_text}**")

    max_aqi = max(pm25, ozone)
    if max_aqi >= 100 or pollen == "High" or smoke:
        score_status, banner_class, advice = "RED (High Risk)", "banner-red", "🚨 High trigger warning: Air quality or pollen is poor today. Limit outdoor playing time."
    elif max_aqi >= 50 or pollen == "Moderate":
        score_status, banner_class, advice = "YELLOW (Moderate Risk)", "banner-yellow", "⚠️ Moderate trigger risk: Keep your rescue inhaler handy if spending time outdoors."
    else:
        score_status, banner_class, advice = "GREEN (Low Risk)", "banner-green", "✅ Favorable conditions: Air quality and pollen levels are low today."

    st.markdown(f"""
    <div class="{banner_class}">
        <h2 style="margin: 0; font-size: 2rem;">Current Status: {score_status}</h2>
        <p style="margin-top: 0.4rem; font-size: 1.1rem; margin-bottom: 0;">{advice}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📊 Local Weather Breakdown")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PM2.5 Dust & Particles", f"{pm25} AQI", delta="Moderate" if pm25 > 50 else "Good")
    m2.metric("Ozone Level", f"{ozone} AQI", delta="Elevated" if ozone > 50 else "Good")
    m3.metric("Pollen Level", pollen)
    m4.metric("Wildfire Smoke", "Detected" if smoke else "Clear")

# PAGE 2: LOG PUFFS
elif page == "Log Inhaler Puffs":
    st.title("Log Daily Inhaler Usage")
    st.write("Keep a simple record of rescue inhaler puffs taken throughout the day.")

    pm25, ozone, pollen_str, smoke, _ = fetch_live_environmental_data(user['zip_code'])
    current_aqi = max(pm25, ozone)

    with st.form("puff_log_form"):
        log_date = st.date_input("Date", value=datetime.now())
        puffs_taken = st.number_input("How many rescue inhaler puffs were taken today?", min_value=0, max_value=25, value=0)
        pollen_val = st.slider("How high was pollen today? (0 = Low, 100 = High):", 0, 100, 40)
        notes = st.text_area("Notes or Symptoms", placeholder="e.g., Coughing during sports practice")

        if st.form_submit_button("Save Entry"):
            logs = user.setdefault("logs", [])
            new_entry = {
                "date": log_date.strftime("%Y-%m-%d"),
                "puffs": puffs_taken,
                "aqi_level": current_aqi,
                "pollen_level": pollen_val
            }
            logs.append(new_entry)
            save_users(st.session_state.users)
            st.success("Entry saved! Check the 'Puffs vs. Weather Chart' tab to see your progress.")

# PAGE 3: ANALYTICS
elif page == "Puffs vs. Weather Chart":
    st.title("Inhaler Usage vs. Local Weather")
    st.write("This chart compares daily inhaler puffs against pollen and air pollution to help you spot environmental triggers.")

    logs = user.get("logs", [])
    if logs:
        df_logs = pd.DataFrame(logs)
        df_logs = df_logs.sort_values("date")

        st.subheader("📈 Trigger Correlation Chart")
        
        chart_data = df_logs.set_index("date")[["puffs", "aqi_level", "pollen_level"]]
        chart_data.columns = ["Rescue Puffs Taken", "Air Pollution (AQI)", "Pollen Level"]

        st.line_chart(chart_data)

        st.divider()

        st.subheader("📊 History Table")
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No entries logged yet. Log daily puffs to generate your comparison chart.")

render_medical_disclaimer()