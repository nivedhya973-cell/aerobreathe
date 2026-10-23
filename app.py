import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Far From Home",
    page_icon="🕊️",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.8rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.15rem;
        text-align: center;
        color: #4B5563;
        margin-bottom: 2rem;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    .about-box {
        background-color: #EBF8FF;
        border-left: 5px solid #3182CE;
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Data Persistence Functions (JSON Storage)
DATA_FILE = "stories.json"

def load_stories():
    if not os.path.exists(DATA_FILE):
        default_stories = [
            {
                "id": 1,
                "title": "Caring for Grandparents Overseas",
                "author": "Anonymous",
                "topic": "Family & Separation",
                "date": "2026-10-20",
                "content": "The hardest part of living here isn't adjusting to the culture—it's the distance when loved ones get sick. Knowing my grandparents are ill overseas while I try to focus on daily life feels like carrying two separate worlds at once. I started this project so none of us have to carry that weight in silence.",
                "relates": 12,
                "hugs": 8,
                "passcode": "1234"
            },
            {
                "id": 2,
                "title": "Caught Between Two Cultures",
                "author": "Elena M.",
                "topic": "Identity & Belonging",
                "date": "2026-10-18",
                "content": "When I visit my home country, people see me as American. But here, people see me as an immigrant. It took years to realize that feeling 'caught in between' isn't a weakness—it's a unique perspective that connects us with millions of others.",
                "relates": 19,
                "hugs": 15,
                "passcode": "1234"
            }
        ]
        with open(DATA_FILE, "w") as f:
            json.dump(default_stories, f, indent=4)
        return default_stories
    
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_stories(stories):
    with open(DATA_FILE, "w") as f:
        json.dump(stories, f, indent=4)

# Load Stories into Session State
if "stories" not in st.session_state:
    st.session_state.stories = load_stories()

# Title Header
st.markdown('<div class="main-title">Far From Home 🕊️</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">A community platform exploring the emotional dimensions of immigration, identity, family separation, and living between two worlds.</div>', 
    unsafe_allow_html=True
)

# Sidebar Navigation
st.sidebar.title("Far From Home")
page = st.sidebar.radio("Explore", ["About the Project", "Read Stories", "Share Your Story", "Community Discussions", "Helpful Resources"])

# PAGE 1: ABOUT THE PROJECT
if page == "About the Project":
    st.header("About Far From Home")
    
    st.markdown("""
    <div class="about-box">
        <h4>Mission & Inspiration</h4>
        <p>Far From Home is a community-centered initiative exploring the psychological and emotional experiences of immigration. Moving to a new country is more than just relocation—it often means navigating identity, growing up between cultures, and dealing with family separation.</p>
        <p>This project was created out of personal family experiences, specifically the emotional weight of caring about sick grandparents living overseas while navigating daily life in a different culture. Far From Home provides a space where immigrants, international students, and multi-generational families can share unspoken experiences and feel understood.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Stories Shared", value=len(st.session_state.stories))
    with col2:
        total_relates = sum(s.get("relates", 0) for s in st.session_state.stories)
        st.metric(label="Total 'I Relate' Reactions", value=total_relates)
    with col3:
        total_hugs = sum(s.get("hugs", 0) for s in st.session_state.stories)
        st.metric(label="Support Hugs Sent", value=total_hugs)

# PAGE 2: READ STORIES
elif page == "Read Stories":
    st.header("Community Stories")
    st.write("Real experiences shared by immigrants, students, and families living between cultures.")

    col_search, col_topic = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Search stories by keyword:", placeholder="e.g., grandparents, culture, language...")
    with col_topic:
        topics = ["All Topics", "Family & Separation", "Identity & Belonging", "Cultural Adjustment", "Intergenerational Differences"]
        selected_topic = st.selectbox("Filter by theme:", topics)

    st.divider()

    # Filter Logic
    filtered_stories = st.session_state.stories
    if selected_topic != "All Topics":
        filtered_stories = [s for s in filtered_stories if s.get("topic") == selected_topic]
    if search_query:
        query = search_query.lower()
        filtered_stories = [
            s for s in filtered_stories 
            if query in s.get("title", "").lower() or query in s.get("content", "").lower() or query in s.get("topic", "").lower()
        ]

    if not filtered_stories:
        st.info("No stories found matching your criteria. Be the first to share one!")

    for idx, story in enumerate(filtered_stories):
        with st.container():
            st.subheader(story.get("title", "Untitled"))
            st.caption(f"**Theme:** {story.get('topic')} | **Shared by:** {story.get('author')} | **Date:** {story.get('date')}")
            st.write(story.get("content", ""))
            
            # Interactive Reactions & Passcode Deletion
            col_r1, col_r2, col_space = st.columns([1.5, 1.5, 3])
            with col_r1:
                if st.button(f"🤝 I Relate ({story.get('relates', 0)})", key=f"relate_{story.get('id', idx)}"):
                    story["relates"] = story.get("relates", 0) + 1
                    save_stories(st.session_state.stories)
                    st.rerun()
            with col_r2:
                if st.button(f"🫂 Send Hug ({story.get('hugs', 0)})", key=f"hug_{story.get('id', idx)}"):
                    story["hugs"] = story.get("hugs", 0) + 1
                    save_stories(st.session_state.stories)
                    st.rerun()

            # Protected Delete Expander
            with st.expander("🗑️ Delete this story (Author Only)"):
                entered_passcode = st.text_input("Enter the passcode you created for this story:", type="password", key=f"pass_{story.get('id', idx)}")
                if st.button("Confirm Delete", key=f"confirm_del_{story.get('id', idx)}"):
                    if entered_passcode == story.get("passcode"):
                        st.session_state.stories = [s for s in st.session_state.stories if s.get("id") != story.get("id")]
                        save_stories(st.session_state.stories)
                        st.success("Story successfully deleted.")
                        st.rerun()
                    else:
                        st.error("Incorrect passcode. Only the original author can delete this post.")

            st.divider()

# PAGE 3: SHARE YOUR STORY
elif page == "Share Your Story":
    st.header("Share Your Experience")
    st.write("Your voice matters. Sharing your story helps others feel seen and less alone in their journey.")

    with st.form("submit_story_form"):
        title = st.text_input("Story Title")
        author = st.text_input("Your Name / Display Name (Leave as 'Anonymous' if preferred)", value="Anonymous")
        topic = st.selectbox("Primary Theme", ["Family & Separation", "Identity & Belonging", "Cultural Adjustment", "Intergenerational Differences", "Other"])
        content = st.text_area("Your Story or Reflection", height=200, help="Feel free to talk about missing family, navigating two cultures, or emotional moments.")
        passcode = st.text_input("Create a Delete Passcode (Used to edit/delete your post later)", type="password", help="Remember this code so you can delete your post if you choose to.")

        submitted = st.form_submit_button("Publish Story")
        if submitted:
            if title and content and passcode:
                new_id = len(st.session_state.stories) + 1
                new_story = {
                    "id": new_id,
                    "title": title,
                    "author": author,
                    "topic": topic,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "content": content,
                    "relates": 0,
                    "hugs": 0,
                    "passcode": passcode
                }
                st.session_state.stories.insert(0, new_story)
                save_stories(st.session_state.stories)
                st.success("Thank you for sharing your story! It is now published in the community feed.")
            else:
                st.error("Please fill in the title, story content, and create a delete passcode.")

# PAGE 4: COMMUNITY DISCUSSIONS
elif page == "Community Discussions":
    st.header("Open Dialogue")
    st.write("A space to ask questions, offer support, or reflect on shared experiences.")

    if "comments" not in st.session_state:
        st.session_state.comments = [
            {"user": "Maya", "text": "How do you all handle the anxiety of being far away during family emergencies?"},
            {"user": "David", "text": "Setting up daily video calls with my parents helped us feel much closer despite the time zones."}
        ]

    for c in st.session_state.comments:
        st.info(f"**{c['user']}:** {c['text']}")

    with st.form("add_comment"):
        user_name = st.text_input("Name", value="Community Member")
        user_msg = st.text_area("Add to the conversation:")
        if st.form_submit_button("Post Message"):
            if user_msg:
                st.session_state.comments.append({"user": user_name, "text": user_msg})
                st.rerun()

# PAGE 5: HELPFUL RESOURCES
elif page == "Helpful Resources":
    st.header("Support & Guidance")
    st.write("Organizations and communities offering mental wellness, legal guidance, and newcomer support.")
    
    st.markdown("""
    * **Mental Health & Wellness:** Counseling services specializing in immigrant adjustment, cross-cultural stress, and family separation.
    * **Family Support Networks:** Peer support groups for families with members living overseas.
    * **Legal & Documentation Assistance:** Pro bono legal clinics for immigration guidance and residency resources.
    """)