import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import date, datetime, timedelta
import urllib.parse

# =========================================================
# 🔑 INPUT YOUR AIRNOW API KEY HERE
# =========================================================
AIRNOW_API_KEY = "D1C21388-5630-4BFC-BAFD-605FFE1C8E2"   # Your EPA AirNow Key

# Page Configuration
st.set_page_config(
    page_title="AeroBreathe — Family Asthma Safety",
    page_icon="🫁",
    layout="wide"
)

# High-Contrast Mobile & Dark-Mode Safe Styling
st.markdown("""
    <style>
    /* Global app palette */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        background-color: #EAF3F2 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Force Dark Text on Labels, Headings, and Prose for Mobile/Dark Mode */
    label, p, h1, h2, h3, h4, h5, h6, .stMarkdown, .stSelectbox label, .stNumberInput label {
        color: #203B43 !important;
        font-weight: 600 !important;
    }

    /* Soft teal input fields with calm blue-green borders */
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {
        background-color: #F7FBFA !important;
        color: #203B43 !important;
        border: 2px solid #78999A !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        padding: 10px !important;
    }

    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #617B80 !important;
        opacity: 1 !important;
    }

    /* Dark Mode Button Overrides (Fixes Blacked-Out Buttons on Phones) */
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background-color: #B8D8CB !important;
        color: #244B43 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
    }

    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #9FC8B8 !important;
        color: #1D433B !important;
    }

    /* Page navigation */
    div[data-testid="stSegmentedControl"] [role="radio"] {
        color: #456D70 !important;
    }

    div[data-testid="stSegmentedControl"] [role="radio"][aria-checked="true"] {
        background-color: #B8D8CB !important;
        color: #244B43 !important;
    }

    /* Feature Cards */
    .feature-card {
        background: #DCEAE8;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #B4CBC7;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        height: 100%;
        margin-bottom: 1rem;
    }

    /* Score Banners */
    .banner-green {
        background-color: #DCFCE7;
        color: #14532D !important;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 6px solid #22C55E;
    }
    .banner-yellow {
        background-color: #FEF3C7;
        color: #713F12 !important;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 6px solid #EAB308;
    }
    .banner-red {
        background-color: #FEE2E2;
        color: #7F1D1D !important;
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
    .call-parent { background-color: #537F98; }
    .call-doctor { background-color: #5E8C79; }

    /* Calendar Link Button */
    .cal-link-btn {
        display: inline-block;
        padding: 0.6rem 1.2rem;
        background-color: #537F98;
        color: white !important;
        border-radius: 8px;
        text-decoration: none !important;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    /* Footer Medical Disclaimer */
    .medical-disclaimer {
        margin-top: 3rem;
        padding: 1rem;
        background-color: #D4E3E0;
        border-radius: 8px;
        border: 1px solid #AFC7C3;
        text-align: center;
        font-size: 0.85rem;
        color: #38565D !important;
    }

    .content-card {
        background: #DCEAE8;
        border: 1px solid #B4CBC7;
        border-radius: 8px;
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
            <strong>⚠️ Medical Disclaimer:</strong> AeroBreathe is an informational tool designed to help families monitor local air quality and track inhaler use. AeroBreathe does not provide medical advice, diagnosis, or treatment. Always consult your doctor or primary healthcare provider regarding any questions about a medical condition or asthma management plan.
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
                calc_pollen = min(100, int(max(pm25, ozone) * 0.85))
                pollen_label = "High" if calc_pollen > 70 else ("Moderate" if calc_pollen > 35 else "Low")
                return pm25, ozone, calc_pollen, pollen_label, False, f"Live EPA AirNow Feed (Zip: {zip_code})"
        except Exception:
            pass

    return 42, 38, 40, "Moderate", False, f"Baseline Environmental Feed (Zip: {zip_code})"

def get_ai_api_key():
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret_key = None
    return secret_key or os.getenv("OPENAI_API_KEY")

def ask_aero_ai(question, context):
    api_key = get_ai_api_key()
    if not api_key:
        return None, "AI is not configured. Set OPENAI_API_KEY in the environment or Streamlit secrets."

    system_prompt = (
        "You are AeroBreathe, an environmental information assistant for caregivers. "
        "You are not a clinician and must not diagnose, assess whether a child is safe to exercise, "
        "or recommend starting, stopping, changing, or timing any medication. For medication questions, "
        "direct the caregiver to the child's written asthma action plan and clinician. For severe or "
        "rapidly worsening breathing symptoms, tell them to follow their emergency plan and seek urgent "
        "medical help. Explain air-quality information in plain language, use only facts in the supplied "
        "context, never invent hourly forecasts or pollutant-specific log data, and distinguish correlation "
        "from causation. Keep the answer concise and practical."
    )
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"},
                ],
                "temperature": 0.3,
            },
            timeout=45,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
        if answer:
            return answer, None
        return None, "The AI service returned an empty response. Please try again."
    except requests.RequestException:
        return None, "The AI service could not be reached. Check the connection and API configuration, then try again."
    except (KeyError, IndexError, TypeError, ValueError):
        return None, "The AI service returned an unreadable response. Please try again."

def generate_doctor_report(logs, today=None):
    today = today or date.today()
    window_start = today - timedelta(days=29)
    recent_entries = []

    for entry in logs:
        try:
            entry_date = datetime.strptime(str(entry["date"]), "%Y-%m-%d").date()
            puffs = max(0, int(float(entry.get("puffs", 0))))
        except (KeyError, TypeError, ValueError):
            continue
        if window_start <= entry_date <= today:
            try:
                aqi = float(entry["aqi_level"])
            except (KeyError, TypeError, ValueError):
                aqi = None
            recent_entries.append((entry_date, puffs, aqi))

    if not recent_entries:
        return (
            f"Doctor visit summary ({window_start:%b %d, %Y} to {today:%b %d, %Y})\n"
            "No valid inhaler log entries were found in the last 30 days."
        )

    total_puffs = sum(puffs for _, puffs, _ in recent_entries)
    logged_days = len({entry_date for entry_date, _, _ in recent_entries})
    total_by_weekday = {}
    for entry_date, puffs, _ in recent_entries:
        weekday = entry_date.strftime("%A")
        total_by_weekday[weekday] = total_by_weekday.get(weekday, 0) + puffs

    lines = [
        f"Doctor visit summary ({window_start:%b %d, %Y} to {today:%b %d, %Y})",
        f"Logged rescue inhaler use: {total_puffs} puffs across {logged_days} logged days ({len(recent_entries)} entries).",
    ]

    aqI_covered_puffs = sum(
        puffs for _, puffs, aqi in recent_entries if aqi is not None and aqi > 70
    )
    comparable_puffs = sum(
        puffs for _, puffs, aqi in recent_entries if aqi is not None
    )
    if comparable_puffs:
        high_aqi_percent = round(aqI_covered_puffs / comparable_puffs * 100)
        lines.append(
            f"Environmental overlap: {aqI_covered_puffs} of {comparable_puffs} puffs "
            f"({high_aqi_percent}%) were logged on entries with stored AQI above 70. "
            "Aero stores the higher of PM2.5 and ozone, so the log cannot identify which pollutant was higher."
        )
    else:
        lines.append("Environmental overlap: no comparable AQI values were recorded with these entries.")

    if total_puffs:
        highest_count = max(total_by_weekday.values())
        busiest_days = [
            weekday for weekday, count in total_by_weekday.items()
            if count == highest_count and count > 0
        ]
        if busiest_days:
            day_label = " and ".join(busiest_days)
            lines.append(f"Highest logged weekday use: {day_label} ({highest_count} puffs).")
    else:
        lines.append("No rescue inhaler puffs were recorded in this period.")

    lines.append("These are user-entered observations, not a diagnosis or proof that air quality caused symptoms.")
    return "\n".join(lines)

# ---------------------------------------------------------
# CALENDAR GENERATOR UTILITIES
# ---------------------------------------------------------
def generate_gcal_link(title, time_str):
    now = datetime.now()
    time_parts = time_str.split(":")
    event_start = datetime(now.year, now.month, now.day, int(time_parts[0]), int(time_parts[1]))
    event_end = datetime(now.year, now.month, now.day, int(time_parts[0]), int(time_parts[1]))
    
    start_fmt = event_start.strftime("%Y%m%dT%H%M00")
    end_fmt = event_end.strftime("%Y%m%dT%H%M00")
    
    params = {
        "action": "TEMPLATE",
        "text": f"🫁 Aero Reminder: {title}",
        "dates": f"{start_fmt}/{end_fmt}",
        "details": "Daily asthma medication and safety reminder via Aero.",
        "recur": "RRULE:FREQ=DAILY"
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

def generate_ics_file(title, time_str):
    now = datetime.now().strftime("%Y%m%d")
    time_clean = time_str.replace(":", "") + "00"
    
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Aero//Asthma Reminder//EN
BEGIN:VEVENT
SUMMARY:🫁 Aero: {title}
DESCRIPTION:Daily asthma medication reminder via Aero.
DTSTART:{now}T{time_clean}
RRULE:FREQ=DAILY
BEGIN:VALARM
TRIGGER:-PT10M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
END:VEVENT
END:VCALENDAR"""

# ---------------------------------------------------------
# PUBLIC LANDING PAGE & ACCOUNT PORTAL
# ---------------------------------------------------------
if not st.session_state.current_user:
    st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem; background: #DCEAE8; border-radius: 16px; border: 1px solid #B4CBC7; margin-bottom: 2rem;">
            <h1 style="font-size: 3rem; color: #203B43; margin: 0;">🫁 AeroBreathe</h1>
            <p style="font-size: 1.3rem; color: #38565D; margin-top: 0.5rem; font-weight: 500;">
                Smart, simple asthma safety and trigger tracking built for families.
            </p>
            <p style="font-size: 1rem; color: #617B80; max-width: 650px; margin: 0.5rem auto 0 auto;">
                Aero translates real-time air quality data into daily action, helping parents track rescue inhaler usage against local pollen and ozone triggers without collecting sensitive personal information.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Core Features Showcase Grid
    st.markdown("### ⚡ Key Features")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        st.markdown("""
            <div class="feature-card">
                <h3 style="margin-top:0; color:#537F98;">📊 Real-Time AQI Feed</h3>
                <p style="font-size:0.95rem; color:#38565D;">Pulls live EPA AirNow PM2.5, Ozone, and pollen metrics for your exact zip code.</p>
            </div>
        """, unsafe_allow_html=True)

    with col_f2:
        st.markdown("""
            <div class="feature-card">
                <h3 style="margin-top:0; color:#5E8C79;">📈 Puff Analytics</h3>
                <p style="font-size:0.95rem; color:#38565D;">Correlates daily rescue inhaler usage against environmental spikes in an interactive chart.</p>
            </div>
        """, unsafe_allow_html=True)

    with col_f3:
        st.markdown("""
            <div class="feature-card">
                <h3 style="margin-top:0; color:#537F98;">📞 One-Tap Calling</h3>
                <p style="font-size:0.95rem; color:#38565D;">Keep optional emergency phone numbers one tap away during flare-ups.</p>
            </div>
        """, unsafe_allow_html=True)

    with col_f4:
        st.markdown("""
            <div class="feature-card">
                <h3 style="margin-top:0; color:#5E8C79;">📅 Calendar Sync</h3>
                <p style="font-size:0.95rem; color:#38565D;">Export daily medication reminders directly into Google Calendar or Apple Calendar.</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 🔑 Access Account")
    tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Create Account"])

    with tab_login:
        st.subheader("Welcome Back")
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
        st.write("Sign up in seconds to start tracking weather triggers.")
        
        with st.form("signup_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                email = st.text_input("Parent Email / Username*", placeholder="e.g., sarah_m")
            with col_a2:
                password = st.text_input("Create Password*", type="password", placeholder="Create password")

            st.divider()
            st.markdown("### 📍 Location & Optional Emergency Contacts")
            zip_code = st.text_input("Home Zip Code*", placeholder="e.g., 78641")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                parent_phone = st.text_input("Parent Phone Number (Optional)", placeholder="e.g., 555-019-2831")
            with col_p2:
                doctor_phone = st.text_input("Doctor Office Phone (Optional)", placeholder="e.g., 555-014-9922")

            signup_submit = st.form_submit_button("Create Account & Enter Dashboard")
            if signup_submit:
                if email and password and zip_code:
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
                            "parent_phone": parent_phone.replace("-", "").replace(" ", "") if parent_phone else "",
                            "doctor_phone": doctor_phone.replace("-", "").replace(" ", "") if doctor_phone else "",
                            "logs": default_logs,
                            "reminders": [
                                {"task": "Morning inhaler dose before school", "time": "07:30"},
                                {"task": "Evening controller inhaler dose", "time": "20:00"}
                            ]
                        }
                        save_users(st.session_state.users)
                        st.session_state.current_user = email
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.error("Account already exists.")
                else:
                    st.error("Please fill in required fields (*).")
    
    render_medical_disclaimer()
    st.stop()

# ---------------------------------------------------------
# LOGGED IN DASHBOARD
# ---------------------------------------------------------
user = st.session_state.users[st.session_state.current_user]

st.sidebar.markdown(f"""
<div style="background: #DCEAE8; padding: 1rem; border-radius: 10px; border: 1px solid #B4CBC7; margin-bottom: 1rem;">
    <h4 style="margin:0; color:#203B43;">Account Overview</h4>
    <p style="margin:0; color:#617B80; font-size:0.9rem;">Zip Code: <strong>{user['zip_code']}</strong></p>
</div>
""", unsafe_allow_html=True)

if user.get("parent_phone") or user.get("doctor_phone"):
    st.sidebar.markdown("### 📞 Direct Calling")
    if user.get("parent_phone"):
        parent_tel = f"tel:{user['parent_phone']}"
        st.sidebar.markdown(f'<a href="{parent_tel}" class="call-btn call-parent">📱 Call Parent ({user["parent_phone"]})</a>', unsafe_allow_html=True)
    if user.get("doctor_phone"):
        doctor_tel = f"tel:{user['doctor_phone']}"
        st.sidebar.markdown(f'<a href="{doctor_tel}" class="call-btn call-doctor">🩺 Call Doctor ({user["doctor_phone"]})</a>', unsafe_allow_html=True)

st.sidebar.divider()
if st.sidebar.button("🚪 Log Out", use_container_width=True):
    st.session_state.current_user = None
    st.rerun()

# TOP NAVIGATION BAR
page = st.segmented_control(
    "Select View",
    ["Today's Air Quality", "Log Inhaler Puffs", "Puffs vs. Weather Chart", "Medication & Reminders", "Aero Assistant"],
    default="Today's Air Quality",
    label_visibility="collapsed"
)

st.write("") 

# PAGE 1: DASHBOARD
if page == "Today's Air Quality":
    st.title("Today's Air Quality & Breathing Risk")
    st.write("Check your local air quality and pollen levels before planning outdoor time.")
    
    pm25, ozone, pollen_val, pollen_str, smoke, source_text = fetch_live_environmental_data(user['zip_code'])
    st.caption(f"📡 Data Source: **{source_text}**")

    max_aqi = max(pm25, ozone)
    if max_aqi >= 100 or pollen_str == "High" or smoke:
        score_status, banner_class, advice = "RED (High Risk)", "banner-red", "🚨 High trigger warning: Air quality or pollen is poor today. Limit outdoor playing time."
    elif max_aqi >= 50 or pollen_str == "Moderate":
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
    m3.metric("Pollen Index", f"{pollen_val} / 100 ({pollen_str})")
    m4.metric("Wildfire Smoke", "Detected" if smoke else "Clear")

# PAGE 2: LOG PUFFS
elif page == "Log Inhaler Puffs":
    st.title("Log Daily Inhaler Usage")
    st.write("Keep a simple record of rescue inhaler puffs taken throughout the day.")

    pm25, ozone, auto_pollen_val, pollen_str, smoke, _ = fetch_live_environmental_data(user['zip_code'])
    current_aqi = max(pm25, ozone)

    st.info(f"📍 **Automatic Environmental Sync (Zip {user['zip_code']}):** AQI: **{current_aqi}** | Pollen Level: **{auto_pollen_val}/100 ({pollen_str})**")

    with st.form("puff_log_form"):
        log_date = st.date_input("Date", value=datetime.now())
        puffs_taken = st.number_input("How many rescue inhaler puffs were taken today?", min_value=0, max_value=25, value=0)
        notes = st.text_area("Notes or Symptoms", placeholder="e.g., Coughing during sports practice")

        if st.form_submit_button("Save Entry"):
            logs = user.setdefault("logs", [])
            new_entry = {
                "date": log_date.strftime("%Y-%m-%d"),
                "puffs": puffs_taken,
                "aqi_level": current_aqi,
                "pollen_level": auto_pollen_val
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

# PAGE 4: MEDICATION & CALENDAR REMINDERS
elif page == "Medication & Reminders":
    st.title("Medication & Calendar Reminders")
    st.write("Set daily reminders and sync them directly with Google Calendar or Apple Calendar for phone alerts.")

    reminders = user.get("reminders", [])
    if reminders:
        st.subheader("📋 Active Reminders & Phone Sync")
        for idx, rem in enumerate(reminders):
            st.markdown(f"""
            <div class="content-card" style="padding: 1.2rem; margin-bottom: 0.8rem; border-left: 5px solid #537F98;">
                <strong style="font-size: 1.1rem; color: #203B43;">⏰ {rem['time']}</strong> — <span style="color: #38565D;">{rem['task']}</span>
            </div>
            """, unsafe_allow_html=True)

            col_s1, col_s2, _ = st.columns([1.5, 1.5, 3])
            with col_s1:
                gcal_url = generate_gcal_link(rem['task'], rem['time'])
                st.markdown(f'<a href="{gcal_url}" target="_blank" class="cal-link-btn">📅 Sync to Google Calendar</a>', unsafe_allow_html=True)
            with col_s2:
                ics_data = generate_ics_file(rem['task'], rem['time'])
                st.download_button(
                    label="📲 Sync to Apple Calendar (.ics)",
                    data=ics_data,
                    file_name=f"Aero_Reminder_{idx+1}.ics",
                    mime="text/calendar",
                    key=f"ics_btn_{idx}"
                )
            st.divider()
    else:
        st.info("No custom reminders added yet. Create one below!")

    st.subheader("➕ Create New Reminder")
    with st.form("add_reminder_form"):
        new_task = st.text_input("Reminder Description", placeholder="e.g., Take Budesonide before school")
        new_time = st.time_input("Scheduled Time", value=datetime.strptime("07:30", "%H:%M").time())
        
        if st.form_submit_button("Save & Enable Calendar Sync"):
            if new_task:
                user.setdefault("reminders", []).append({
                    "task": new_task,
                    "time": new_time.strftime("%H:%M")
                })
                save_users(st.session_state.users)
                st.success("Custom reminder saved!")
                st.rerun()

elif page == "Aero Assistant":
    st.title("Aero Assistant")
    st.write("Environmental information and visit preparation for your family.")
    st.caption(
        "AI responses are informational, not medical advice. When submitted, your question and relevant "
        "readings or summarized log data are sent to OpenAI. Doctor-report calculations are performed locally."
    )

    pm25, ozone, pollen_val, pollen_str, smoke, source_text = fetch_live_environmental_data(user["zip_code"])
    current_environment = (
        f"Current feed: PM2.5 AQI {pm25}; ozone AQI {ozone}; pollen index {pollen_val}/100 ({pollen_str}); "
        f"wildfire smoke {'detected' if smoke else 'not detected'}; source: {source_text}. "
        "These are current readings, not an hourly forecast."
    )
    recent_report = generate_doctor_report(user.get("logs", []))

    outdoor_tab, visit_tab, terms_tab, report_tab = st.tabs(
        ["Outdoor Advisor", "Visit Prep", "Explain a Term", "Doctor Report"]
    )

    with outdoor_tab:
        st.caption(current_environment)
        with st.form("outdoor_advisor_form"):
            outdoor_question = st.text_area(
                "What activity and time are you planning?",
                placeholder="For example: Is an outdoor soccer practice at 4 PM a good idea today?",
                key="outdoor_advisor_question",
            )
            outdoor_submit = st.form_submit_button("Get Environmental Guidance")
        if outdoor_submit:
            if outdoor_question.strip():
                answer, error = ask_aero_ai(outdoor_question, current_environment)
                st.session_state["aero_outdoor_answer"] = answer
                st.session_state["aero_outdoor_error"] = error
            else:
                st.warning("Enter an activity or question first.")
        if st.session_state.get("aero_outdoor_answer"):
            st.markdown(st.session_state["aero_outdoor_answer"])
        elif st.session_state.get("aero_outdoor_error"):
            st.info(st.session_state["aero_outdoor_error"])

    with visit_tab:
        st.markdown("Share what is on your mind, and Aero can help organize questions for your clinician.")
        with st.form("visit_prep_form"):
            visit_question = st.text_area(
                "What would you like to prepare for?",
                placeholder="For example: What should I ask at our asthma check-up tomorrow?",
                key="visit_prep_question",
            )
            visit_submit = st.form_submit_button("Prepare Questions")
        if visit_submit:
            if visit_question.strip():
                answer, error = ask_aero_ai(
                    visit_question,
                    f"Recent log summary for context:\n{recent_report}",
                )
                st.session_state["aero_visit_answer"] = answer
                st.session_state["aero_visit_error"] = error
            else:
                st.warning("Enter a question or concern first.")
        if st.session_state.get("aero_visit_answer"):
            st.markdown(st.session_state["aero_visit_answer"])
        elif st.session_state.get("aero_visit_error"):
            st.info(st.session_state["aero_visit_error"])

    with terms_tab:
        with st.form("term_explainer_form"):
            term_question = st.text_area(
                "Which air-quality or medical term should Aero explain?",
                placeholder="For example: What is PM2.5, and why can it affect breathing?",
                key="term_explainer_question",
            )
            term_submit = st.form_submit_button("Explain")
        if term_submit:
            if term_question.strip():
                answer, error = ask_aero_ai(term_question, "No personal log data is needed for this explanation.")
                st.session_state["aero_term_answer"] = answer
                st.session_state["aero_term_error"] = error
            else:
                st.warning("Enter a term or question first.")
        if st.session_state.get("aero_term_answer"):
            st.markdown(st.session_state["aero_term_answer"])
        elif st.session_state.get("aero_term_error"):
            st.info(st.session_state["aero_term_error"])

    with report_tab:
        st.write("Create a concise, data-grounded summary for your child's next appointment.")
        if st.button("Generate Doctor Report", key="generate_doctor_report"):
            report = generate_doctor_report(user.get("logs", []))
            st.session_state["aero_doctor_report"] = report
            answer, error = ask_aero_ai(
                "Prepare a concise pediatrician-ready version of this report. Preserve every number and caveat exactly. Do not add diagnoses or claim that an environmental reading caused inhaler use.",
                report,
            )
            st.session_state["aero_doctor_report_ai"] = answer
            st.session_state["aero_doctor_report_error"] = error

        if st.session_state.get("aero_doctor_report"):
            st.markdown("#### Calculated Summary")
            st.text(st.session_state["aero_doctor_report"])
            if st.session_state.get("aero_doctor_report_ai"):
                st.markdown("#### AI-Prepared Version")
                st.markdown(st.session_state["aero_doctor_report_ai"])
            elif st.session_state.get("aero_doctor_report_error"):
                st.info(
                    f"The calculated summary is ready. {st.session_state['aero_doctor_report_error']}"
                )

render_medical_disclaimer()