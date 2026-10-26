import streamlit as st
import pandas as pd
import json
import os
import hashlib
import hmac
import requests
from datetime import date, datetime, timedelta
import urllib.parse

# =========================================================
# KEYS ARE READ FROM .streamlit/secrets.toml (or environment)
# GROQ_API_KEY = "gsk_..."
# AIRNOW_API_KEY = "your-airnow-key"
# =========================================================
def get_secret(name):
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.getenv(name)

AIRNOW_API_KEY = get_secret("AIRNOW_API_KEY")

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
    div[data-testid="stSegmentedControl"] button,
    div[data-testid="stSegmentedControl"] [role="radio"],
    button[data-testid="stBaseButton-segmented_control"] {
        background-color: #A9C7D6 !important;
        color: #203B43 !important;
        border-color: #78999A !important;
    }

    div[data-testid="stSegmentedControl"] button:hover,
    button[data-testid="stBaseButton-segmented_control"]:hover {
        background-color: #8FB4C7 !important;
        color: #1D433B !important;
    }

    div[data-testid="stSegmentedControl"] [role="radio"][aria-checked="true"],
    button[data-testid="stBaseButton-segmented_controlActive"] {
        background-color: #537F98 !important;
        color: #FFFFFF !important;
        border-color: #537F98 !important;
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
    .banner-green h2, .banner-yellow h2, .banner-red h2 {
        color: inherit !important;
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
    # Demo data is never written to disk
    if st.session_state.get("demo"):
        return
    try:
        with open(USER_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except OSError:
        st.warning("Could not save your data right now. Please try again.")

def hash_password(pw, salt=None):
    salt = salt or os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()
    return f"{salt}${h}"

def check_password(pw, stored):
    if "$" not in stored:  # legacy plaintext accounts still work
        return hmac.compare_digest(pw, stored)
    salt, h = stored.split("$", 1)
    return hmac.compare_digest(hash_password(pw, salt).split("$", 1)[1], h)

def build_demo_user():
    """14 days of believable data with a visible ozone spike. Dates are relative to today."""
    rows = [  # (puffs, AQI, note) oldest -> newest
        (0, 34, ""), (1, 41, ""), (0, 38, ""), (0, 36, ""), (1, 47, ""),
        (0, 44, ""), (2, 78, "Cough after recess"),
        (5, 112, "High ozone day. Wheezing at soccer practice, stayed inside after"),
        (4, 98, "Night cough, woke once"), (2, 66, "Better, still a little tight"),
        (1, 52, ""), (0, 40, ""), (1, 45, ""), (1, 43, ""),
    ]
    today = date.today()
    logs = [
        {"date": (today - timedelta(days=len(rows) - 1 - i)).strftime("%Y-%m-%d"),
         "puffs": p, "aqi_level": a, "notes": n}
        for i, (p, a, n) in enumerate(rows)
    ]
    return {
        "password": "", "zip_code": "78641",
        "parent_phone": "5550142", "doctor_phone": "5550175",  # 555-01xx = fictional range
        "logs": logs,
        "reminders": [
            {"task": "Morning controller inhaler (per asthma action plan)", "time": "07:30"},
            {"task": "Evening controller inhaler (per asthma action plan)", "time": "20:00"},
        ],
    }

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
# LIVE AIR QUALITY (AirNow first, Open-Meteo fallback, cached 30 min)
# Exceptions are NOT cached, so a failed fetch retries on the next click.
# ---------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner="Fetching air quality…")
def _fetch_env(zip_code):
    if AIRNOW_API_KEY:
        try:
            r = requests.get(
                "https://www.airnowapi.org/aq/observation/zipCode/current/",
                params={"format": "application/json", "zipCode": zip_code,
                        "distance": 25, "API_KEY": AIRNOW_API_KEY},
                timeout=6,
            )
            r.raise_for_status()
            rows = r.json()
            pm25 = next((x["AQI"] for x in rows if x["ParameterName"] == "PM2.5"), None)
            ozone = next((x["AQI"] for x in rows if x["ParameterName"] == "O3"), None)
            if rows and (pm25 is not None or ozone is not None):
                o = rows[0]
                return {
                    "pm25": pm25, "ozone": ozone, "source": "EPA AirNow",
                    "observed": f"{o['DateObserved'].strip()} {int(o['HourObserved']):02d}:00 {o['LocalTimeZone']}",
                }
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass  # fall through to Open-Meteo

    geo = requests.get(f"https://api.zippopotam.us/us/{zip_code}", timeout=6)
    geo.raise_for_status()
    place = geo.json()["places"][0]
    aq = requests.get(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={"latitude": place["latitude"], "longitude": place["longitude"],
                "current": "us_aqi_pm2_5,us_aqi_ozone", "timezone": "auto"},
        timeout=6,
    )
    aq.raise_for_status()
    cur = aq.json()["current"]
    return {
        "pm25": cur.get("us_aqi_pm2_5"), "ozone": cur.get("us_aqi_ozone"),
        "source": "Open-Meteo Air Quality",
        "observed": cur["time"].replace("T", " ") + " (local)",
    }

def fetch_live_environmental_data(zip_code):
    """Returns (env_dict, None) or (None, friendly_error). Never raises."""
    try:
        env = _fetch_env(str(zip_code).strip())
        if env["pm25"] is None and env["ozone"] is None:
            raise ValueError("no readings")
        return env, None
    except Exception:
        return None, "Air-quality data is temporarily unavailable. Please try again in a few minutes."

def max_aqi_of(env):
    return max(v for v in (env["pm25"], env["ozone"]) if v is not None)

def risk_level(env):
    """Word + color + one action. Deliberately says nothing about medication timing."""
    m = max_aqi_of(env)
    if m >= 100:
        return "RED", "banner-red", "Limit outdoor time and follow your child's asthma action plan."
    if m >= 50:
        return "YELLOW", "banner-yellow", "Outdoor play is okay. Keep the rescue inhaler in the backpack and watch for symptoms."
    return "GREEN", "banner-green", "Good day to be outside. Keep the rescue inhaler with you as usual."

# ---------------------------------------------------------
# AI (GROQ) HELPERS
# ---------------------------------------------------------
def get_ai_api_key():
    return get_secret("GROQ_API_KEY")

def ask_aero_ai(question, context):
    api_key = get_ai_api_key()
    if not api_key:
        return None, "AI is not configured. Set GROQ_API_KEY in the environment or Streamlit secrets."

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
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
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
        return None, "The AI assistant is temporarily unavailable. Please try again in a moment."
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

    high_aqi_puffs = sum(
        puffs for _, puffs, aqi in recent_entries if aqi is not None and aqi > 70
    )
    comparable_puffs = sum(
        puffs for _, puffs, aqi in recent_entries if aqi is not None
    )
    if comparable_puffs:
        high_aqi_percent = round(high_aqi_puffs / comparable_puffs * 100)
        lines.append(
            f"Environmental overlap: {high_aqi_puffs} of {comparable_puffs} puffs "
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
    hh, mm = (int(p) for p in time_str.split(":")[:2])
    event_start = datetime(now.year, now.month, now.day, hh, mm)
    event_end = event_start + timedelta(minutes=15)

    params = {
        "action": "TEMPLATE",
        "text": f"🫁 Aero Reminder: {title}",
        "dates": f"{event_start:%Y%m%dT%H%M00}/{event_end:%Y%m%dT%H%M00}",
        "details": "Daily asthma reminder via Aero.",
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
UID:{now}{time_clean}-{abs(hash(title))}@aerobreathe
DTSTAMP:{now}T{time_clean}
SUMMARY:🫁 Aero: {title}
DESCRIPTION:Daily asthma reminder via Aero.
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
    <div style="text-align: center; padding: 2rem 1rem; background: #DCEAE8; border-radius: 16px; border: 1px solid #B4CBC7; margin-bottom: 1rem;">
        <h1 style="font-size: 3rem; color: #203B43; margin: 0;">🫁 AeroBreathe</h1>
        <p style="font-size: 1.3rem; color: #38565D; margin-top: 0.5rem; font-weight: 500;">
            Smart, simple asthma safety and trigger tracking built for families.
        </p>
        <p style="font-size: 1rem; color: #617B80; max-width: 700px; margin: 0.5rem auto 0 auto;">
            Aero translates local air-quality readings into a daily action and lets parents compare rescue inhaler use against air quality. It stores only what it needs to run: your email, ZIP code, optional phone numbers, and the entries you log. Nothing is sold or shared.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("▶ View Live Demo — no sign-up needed", type="primary", use_container_width=True):
        st.session_state.demo = True
        st.session_state.current_user = "demo"
        st.session_state.demo_user = build_demo_user()
        st.rerun()
    st.caption("If the app was asleep, the first load can take up to a minute. Thanks for your patience!")

    # Core Features Showcase Grid
    st.markdown("### ⚡ Key Features")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        st.markdown("""
        <div class="feature-card">
            <h3 style="margin-top:0; color:#537F98;">📊 Live Air Quality</h3>
            <p style="font-size:0.95rem; color:#38565D;">Pulls current EPA AirNow PM2.5 and ozone readings for your ZIP code.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_f2:
        st.markdown("""
        <div class="feature-card">
            <h3 style="margin-top:0; color:#5E8C79;">📈 Puff Analytics</h3>
            <p style="font-size:0.95rem; color:#38565D;">Compares daily rescue inhaler usage against air quality so patterns are easy to spot.</p>
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
            <p style="font-size:0.95rem; color:#38565D;">Export daily reminders directly into Google Calendar or Apple Calendar.</p>
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
            u = st.session_state.users.get(login_email)
            if u and check_password(login_pass, u["password"]):
                st.session_state.demo = False
                st.session_state.current_user = login_email
                st.success("Log in successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab_signup:
        st.subheader("Create an Account")
        st.write("Sign up in seconds to start tracking air-quality triggers.")

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
                        st.session_state.demo = False
                        st.session_state.users[email] = {
                            "password": hash_password(password),
                            "zip_code": zip_code.strip(),
                            "parent_phone": parent_phone.replace("-", "").replace(" ", "") if parent_phone else "",
                            "doctor_phone": doctor_phone.replace("-", "").replace(" ", "") if doctor_phone else "",
                            "logs": [],
                            "reminders": [
                                {"task": "Morning inhaler (per asthma action plan)", "time": "07:30"},
                                {"task": "Evening inhaler (per asthma action plan)", "time": "20:00"}
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
if st.session_state.get("demo"):
    user = st.session_state.get("demo_user") or build_demo_user()
    st.session_state.demo_user = user
    st.sidebar.info("🎬 Demo profile (ZIP 78641). Changes aren't saved.")
else:
    user = st.session_state.users.get(st.session_state.current_user)
    if user is None:  # users.json was reset (free hosting) or account removed
        st.session_state.current_user = None
        st.rerun()

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
if st.sidebar.button("🚪 Log Out" if not st.session_state.get("demo") else "🚪 Exit Demo", use_container_width=True):
    st.session_state.current_user = None
    st.session_state.demo = False
    st.rerun()

# TOP NAVIGATION BAR
page = st.segmented_control(
    "Select View",
    ["Today's Air Quality", "Log Inhaler Puffs", "Puffs vs. Weather Chart", "Medication & Reminders", "Aero Assistant"],
    default="Today's Air Quality",
    label_visibility="collapsed"
)
page = page or "Today's Air Quality"

st.write("")

# PAGE 1: DASHBOARD
if page == "Today's Air Quality":
    st.title("Today's Air Quality & Breathing Risk")
    st.write("Check your local air quality before planning outdoor time.")

    env, env_error = fetch_live_environmental_data(user["zip_code"])
    if env_error:
        st.warning(env_error)
        if st.button("Try again"):
            st.cache_data.clear()
            st.rerun()
    else:
        st.caption(
            f"📡 Data: **{env['source']}** · Observed {env['observed']} · "
            f"refreshed at most every 30 min"
        )
        word, banner_class, action = risk_level(env)
        st.markdown(f"""
        <div class="{banner_class}">
            <h2 style="margin: 0; font-size: 1.8rem;">{word} — {action}</h2>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.subheader("📊 Local Air Quality")
        m1, m2 = st.columns(2)
        fmt = lambda v: "n/a" if v is None else f"{v} AQI"
        m1.metric("PM2.5 (dust & smoke particles)", fmt(env["pm25"]),
                  delta=None if env["pm25"] is None else ("Moderate or higher" if env["pm25"] > 50 else "Good"),
                  delta_color="off")
        m2.metric("Ozone", fmt(env["ozone"]),
                  delta=None if env["ozone"] is None else ("Elevated" if env["ozone"] > 50 else "Good"),
                  delta_color="off")

# PAGE 2: LOG PUFFS
elif page == "Log Inhaler Puffs":
    st.title("Log Daily Inhaler Usage")
    st.write("Keep a simple record of rescue inhaler puffs taken throughout the day.")

    env, env_error = fetch_live_environmental_data(user["zip_code"])
    current_aqi = max_aqi_of(env) if env else None
    if env:
        st.info(f"📍 Current AQI for ZIP {user['zip_code']}: **{current_aqi}** ({env['source']}). "
                "AQI is saved only for entries dated today.")
    else:
        st.warning(env_error + " You can still save an entry without an AQI value.")

    with st.form("puff_log_form"):
        log_date = st.date_input("Date", value=date.today(), max_value=date.today())
        puffs_taken = st.number_input("Rescue inhaler puffs taken", min_value=0, max_value=25, value=0)
        notes = st.text_area("Notes or Symptoms", placeholder="e.g., Coughing during sports practice")

        if st.form_submit_button("Save Entry"):
            user.setdefault("logs", []).append({
                "date": log_date.strftime("%Y-%m-%d"),
                "puffs": int(puffs_taken),
                "aqi_level": current_aqi if log_date == date.today() else None,
                "notes": notes.strip(),
            })
            save_users(st.session_state.users)
            st.success("Entry saved! Check the 'Puffs vs. Weather Chart' tab to see your progress.")

# PAGE 3: ANALYTICS
elif page == "Puffs vs. Weather Chart":
    st.title("Inhaler Usage vs. Air Quality")
    st.write("Compare rescue inhaler puffs against local air quality to help spot environmental triggers.")

    logs = user.get("logs", [])
    if logs:
        df = pd.DataFrame(logs)
        if "aqi_level" not in df:
            df["aqi_level"] = None
        if "notes" not in df:
            df["notes"] = ""
        df["aqi_level"] = pd.to_numeric(df["aqi_level"], errors="coerce")
        df = df.sort_values("date")

        hi = df[df["aqi_level"] > 70]["puffs"]
        lo = df[df["aqi_level"] <= 70]["puffs"]
        if len(hi) and len(lo):
            st.info(
                f"On entries with AQI above 70, rescue puffs averaged **{hi.mean():.1f}** "
                f"vs **{lo.mean():.1f}** on other days. This is a pattern in your own log, "
                "not proof that air quality caused symptoms."
            )

        st.subheader("🫁 Rescue puffs per entry")
        st.bar_chart(df.set_index("date")["puffs"], color="#537F98")
        st.subheader("🌫️ Air quality (AQI) on those days")
        st.line_chart(df.set_index("date")["aqi_level"], color="#B45309")
        st.caption("AQI above 100 is unhealthy for sensitive groups, including people with asthma.")

        st.divider()
        st.subheader("📊 History Table")
        st.dataframe(df[["date", "puffs", "aqi_level", "notes"]], use_container_width=True)
    else:
        st.info("No entries logged yet. Log daily puffs to generate your comparison chart, or try the demo from the landing page.")

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
        new_task = st.text_input("Reminder Description", placeholder="e.g., Morning inhaler per asthma action plan")
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

# PAGE 5: AERO ASSISTANT
elif page == "Aero Assistant":
    st.title("Aero Assistant")
    st.write("Environmental information and visit preparation for your family.")
    st.caption(
        "AI responses are informational, not medical advice. When submitted, your question and relevant "
        "readings or summarized log data are sent to Groq. Doctor-report calculations are performed locally."
    )

    env, env_error = fetch_live_environmental_data(user["zip_code"])
    if env:
        current_environment = (
            f"Current feed: PM2.5 AQI {env['pm25']}; ozone AQI {env['ozone']}; "
            f"source: {env['source']}, observed {env['observed']}. "
            "These are current readings, not an hourly forecast."
        )
    else:
        current_environment = "Live air-quality readings are unavailable right now."
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
                    with st.spinner("Thinking…"):
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
                    with st.spinner("Thinking…"):
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
                    with st.spinner("Thinking…"):
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
            with st.spinner("Preparing report…"):
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