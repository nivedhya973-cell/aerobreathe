import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(
    page_title="ClearBreathe — Asthma & Environmental Safety",
    page_icon="🫁",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .score-green {
        background-color: #DEF7EC;
        border-left: 6px solid #0E9F6E;
        padding: 1.2rem;
        border-radius: 8px;
        color: #03543F;
    }
    .score-yellow {
        background-color: #FEF08A;
        border-left: 6px solid #CA8A04;
        padding: 1.2rem;
        border-radius: 8px;
        color: #713F12;
    }
    .score-red {
        background-color: #FDE8E8;
        border-left: 6px solid #E02424;
        padding: 1.2rem;
        border-radius: 8px;
        color: #9B1C1C;
    }
    .action-box {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #D1D5DB;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CORE LOGIC: Unified Breathing Score Engine
# ---------------------------------------------------------
def calculate_breathing_score(pm25_aqi, ozone_aqi, pollen_level, smoke_flag):
    """
    Consolidates PM2.5, Ozone, Pollen, and Smoke into a unified Breathing Score:
    - Green: Good conditions
    - Yellow: Moderate conditions (caution for sensitive children)
    - Red: Unhealthy conditions (action plan required)
    """
    max_aqi = max(pm25_aqi, ozone_aqi)
    
    if max_aqi >= 150 or pollen_level == "High" or smoke_flag:
        return "RED", "score-red", "🚨 High Air Hazard: Severe trigger warning across PM2.5/Pollen/Smoke. Follow Yellow/Red Action Plan steps."
    elif max_aqi >= 80 or pollen_level == "Moderate":
        return "YELLOW", "score-yellow", "⚠️ Moderate Trigger Warning: Consider pre-medicating before outdoor physical activity."
    else:
        return "GREEN", "score-green", "✅ Favorable Conditions: Low environmental asthma trigger risk detected."

# Sidebar Header & Quick Emergency Buttons
st.sidebar.title("🫁 ClearBreathe")
st.sidebar.markdown("**Child Profile:** Alex (Age 12)")

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
page = st.sidebar.radio("Navigation", ["Daily Breathing Score", "Outlook & Alerts", "Trigger Diary (v2 Preview)", "Asthma Action Plan"])

# ---------------------------------------------------------
# PAGE 1: DAILY BREATHING SCORE
# ---------------------------------------------------------
if page == "Daily Breathing Score":
    st.title("Today's Unified Breathing Score")
    st.caption("Consolidating pollen, ozone, PM2.5, and smoke data into a single actionable metric.")

    # Location Input / Environmental Data Controls
    col_loc1, col_loc2 = st.columns([2, 1])
    with col_loc1:
        zip_code = st.text_input("Enter Zip Code:", value="78641")
    with col_loc2:
        st.write("")
        st.write("")
        st.caption(f"Showing data for Zip: **{zip_code}**")

    # Mock Environmental API Inputs (Fetchable via AirNow / Open-Meteo APIs in production)
    pm25 = 45        # PM2.5 AQI
    ozone = 62       # Ozone AQI
    pollen = "Moderate" # Cedar/Oak pollen indicator
    smoke = False    # Wildfire smoke detector

    score, css_class, summary = calculate_breathing_score(pm25, ozone, pollen, smoke)

    # Display Unified Score Banner
    st.markdown(f"""
    <div class="{css_class}">
        <h2>Current Status: {score}</h2>
        <p style="font-size: 1.1rem; margin-bottom: 0;">{summary}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Breakdown Metrics
    st.subheader("Environmental Factors Breakdown")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(label="PM2.5 Particles", value=f"{pm25} AQI", delta="Moderate" if pm25 > 50 else "Good")
    m2.metric(label="Ozone Level", value=f"{ozone} AQI", delta="Caution" if ozone > 50 else "Good")
    m3.metric(label="Pollen (Cedar/Oak)", value=pollen, delta="Rising")
    m4.metric(label="Wildfire Smoke", value="Clear" if not smoke else "Detected")

    st.divider()

    # Backpack & School Readiness Checklist
    st.subheader("🎒 Morning School Readiness Checklist")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.checkbox("Rescue Inhaler (Albuterol) in backpack", value=True)
    with c2:
        st.checkbox("Spacer device attached", value=True)
    with c3:
        st.checkbox("Asthma Action Plan copy with school nurse", value=True)

# ---------------------------------------------------------
# PAGE 2: OUTLOOK & ALERTS
# ---------------------------------------------------------
elif page == "Outlook & Alerts":
    st.title("Tomorrow & Weekend Outlook")
    st.write("Plan outdoor activities, soccer matches, and trips around projected air quality triggers.")

    # 3-Day Forecast Table
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
    df_forecast = pd.DataFrame(forecast_data)
    st.table(df_forecast)

    st.divider()

    st.subheader("🔔 Notification Settings")
    st.time_input("Morning Backpack & Air Quality Alert Time:", value=datetime.strptime("07:15", "%H:%M").time())
    st.time_input("Evening Next-Day Risk Alert Time:", value=datetime.strptime("20:00", "%H:%M").time())
    
    st.selectbox("Personal Sensitivity Threshold:", ["Alert on Yellow & Red Days (Recommended for Moderate/Severe)", "Alert on Red Days Only"])

# ---------------------------------------------------------
# PAGE 3: TRIGGER DIARY & TRACKERS (v2 PREVIEW)
# ---------------------------------------------------------
elif page == "Trigger Diary (v2 Preview)":
    st.title("Trigger Diary & Inhaler Tracking")
    st.write("Track daily symptoms to correlate personal triggers against regional pollen and air quality graphs.")

    with st.form("diary_form"):
        st.subheader("Log Today's Symptoms")
        symptom_score = st.slider("Daily Symptom Rating (0 = None, 3 = Severe):", 0, 3, 1)
        rescue_puffs = st.number_input("Rescue Inhaler Puffs Used Today:", min_value=0, max_value=20, value=1)
        notes = st.text_area("Notes (e.g., played outdoor recess, coughing after running):")
        
        submitted = st.form_submit_button("Log Entry")
        if submitted:
            st.success("Entry recorded. Data will populate the doctor's monthly summary timeline.")

    st.divider()

    st.subheader("💊 Medication Counters")
    col_med1, col_med2 = st.columns(2)
    with col_med1:
        st.metric(label="Rescue Inhaler Doses Remaining", value="142 / 200", delta="-2 today")
        st.progress(142 / 200)
    with col_med2:
        st.metric(label="Controller Inhaler Streak", value="14 Days 🔥", delta="Daily Preventive")

# ---------------------------------------------------------
# PAGE 4: ASTHMA ACTION PLAN
# ---------------------------------------------------------
elif page == "Asthma Action Plan":
    st.title("Digital Asthma Action Plan")
    st.write("Direct instructions from your child's physician categorized by risk zone.")

    st.subheader("🟢 Green Zone: Doing Well")
    st.info("• Take Flovent 2 puffs every morning and night.\n• Use Albuterol 2 puffs 15 minutes before PE or exercise.")

    st.subheader("🟡 Yellow Zone: Caution / Symptoms Present")
    st.warning("• Coughing, wheezing, or Yellow Breathing Score day.\n• Continue controller medication.\n• Add Albuterol 2 puffs every 4 hours as needed.")

    st.subheader("🔴 Red Zone: Medical Alert / Severe Symptoms")
    st.error("• Severe breathing trouble, talking in short phrases.\n• Take Albuterol 4 puffs immediately.\n• Contact physician or proceed to urgent care/ER if symptoms do not improve within 15 minutes.")