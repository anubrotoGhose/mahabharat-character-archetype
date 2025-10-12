import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.database import Database
from utils.visualization import (
    create_radar_chart, 
    create_bar_chart, 
    create_comparison_chart,
    create_multi_character_radar,
    create_progress_gauge
)
import base64
from pathlib import Path

st.set_page_config(
    page_title="Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

# Function to encode image to base64
def get_base64_image(image_path):
    """Convert image to base64 for CSS background"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Custom CSS with background image
bg_image = get_base64_image("assets/images/13422928.jpg")

if bg_image:
    st.markdown(f"""
    <style>
        .main {{
            background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)),
                        url("data:image/jpeg;base64,{bg_image}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .dashboard-header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            text-align: center;
            border: 2px solid rgba(102, 126, 234, 0.3);
        }}
        .session-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .session-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .stExpander {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #667eea;
        }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .dashboard-header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            text-align: center;
            border: 2px solid rgba(102, 126, 234, 0.3);
        }}
        .session-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .session-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
    </style>
    """, unsafe_allow_html=True)

def load_session_data(session_id):
    """Load data for a specific session"""
    db = Database()
    responses = db.get_session_responses(session_id)
    return responses

def display_session_list(username):
    """Display list of all sessions for a user by username"""
    db = Database()
    sessions = db.get_user_sessions_by_username(username)
    
    if not sessions:
        st.info("📝 No past sessions found. Complete an assessment to see your history.")
        return None
    
    st.write("### 📚 Your Past Sessions")
    st.write(f"Showing sessions for: **{username}**")
    
    selected_session = None
    
    for idx, session in enumerate(sessions):
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"""
                <div class="session-card">
                    <h4>📝 Session #{idx + 1}</h4>
                    <p style="font-size: 12px; color: #666;">ID: {session['id'][:12]}...</p>
                    <p>📅 {session['created_at']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.write(f"**{session['completed']}** characters completed")
                completion_pct = (session['completed'] / 3) * 100  # Assuming 3 total characters
                st.progress(min(completion_pct / 100, 1.0))
            
            with col3:
                if st.button("👁️ View", key=f"view_{session['id']}", use_container_width=True):
                    selected_session = session['id']
                    st.session_state.selected_session = selected_session
    
    return selected_session

def display_dashboard(responses, session_info=None):
    """Display complete dashboard for a session"""
    
    # Header with Krishna-Arjuna theme
    username = st.session_state.get('username', 'User')
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>🎭 Character Assessment Dashboard</h1>
        <p style="font-size: 18px;">Welcome, {username}!</p>
        <p>Discover your inner strength through the wisdom of Mahabharata</p>
        <p style="font-size: 14px; opacity: 0.9;">✨ "योगः कर्मसु कौशलम्" - Excellence in action is Yoga ✨</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not responses:
        st.warning("📝 No assessment data found. Please complete at least one character assessment.")
        if st.button("Start Assessment"):
            st.switch_page("app.py")
        return
    
    # Overall metrics
    st.write("## 📈 Overall Summary")
    
    avg_rating = sum([r['analysis']['overall_rating'] for r in responses]) / len(responses)
    highest_character = max(responses, key=lambda x: x['analysis']['overall_rating'])
    total_strengths = sum([len(r['analysis'].get('strengths', [])) for r in responses])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #667eea;">🎭 {len(responses)}</h2>
            <p>Characters Assessed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #28a745;">{avg_rating:.1f}/10</h2>
            <p>Average Rating</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #ffc107;">⭐ {highest_character['character_name']}</h2>
            <p>Strongest Archetype</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #17a2b8;">💪 {total_strengths}</h2>
            <p>Total Strengths</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    
    # Overall rating gauge
    col1, col2 = st.columns([1, 2])
    with col1:
        fig = create_progress_gauge(avg_rating)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("### 🌟 Your Journey")
        st.write(f"""
        You have completed assessments for **{len(responses)} character(s)** from the Mahabharata. 
        Your average alignment score is **{avg_rating:.1f}/10**, showing your connection to these 
        timeless archetypes.
        
        **Strongest Alignment:** {highest_character['character_name']} ({highest_character['analysis']['overall_rating']:.1f}/10)
        
        Continue exploring to discover more about your professional personality!
        """)
    
    # Overall comparison charts
    st.write("---")
    st.write("## 📊 Comparative Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_bar_chart(responses)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = create_comparison_chart(responses)
        st.plotly_chart(fig, use_container_width=True)
    
    # Multi-character radar comparison
    if len(responses) > 1:
        st.write("### 🕸️ Multi-Character Quality Comparison")
        fig = create_multi_character_radar(responses)
        st.plotly_chart(fig, use_container_width=True)
    
    # Individual character analysis
    st.write("---")
    st.write("## 🎭 Individual Character Deep Dive")

    for idx, response in enumerate(responses):
        with st.expander(f"**{response['character_name']}** - Rating: {response['analysis']['overall_rating']:.1f}/10", expanded=False):
            
            # Overall rating gauge
            col1, col2 = st.columns([1, 2])
            
            with col1:
                fig = create_progress_gauge(response['analysis']['overall_rating'])
                st.plotly_chart(fig, use_container_width=True, 
                            key=f"char_gauge_{response['character_id']}_{idx}_{response.get('created_at', '')}")
            
            with col2:
                st.write(f"### Assessment Summary")
                st.write(f"**Character:** {response['character_name']}")
                st.write(f"**Overall Rating:** {response['analysis']['overall_rating']:.1f}/10")
                st.write(f"**Passage Read:** {'✅ Yes' if response['read_passage'] else '❌ No'}")
                st.write(f"**Completed:** {response['created_at']}")
            
            st.write("---")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("### 💪 Strengths")
                for strength in response['analysis'].get('strengths', []):
                    st.write(f"✓ {strength}")
                
                st.write("### 🎯 Areas for Improvement")
                for area in response['analysis'].get('areas_for_improvement', []):
                    st.write(f"○ {area}")
            
            with col2:
                st.write("### 💡 Recommendations")
                for rec in response['analysis'].get('recommendations', []):
                    st.write(f"→ {rec}")
                
                st.write("### 🔍 Key Insights")
                for insight in response['analysis'].get('key_insights', []):
                    st.write(f"• {insight}")
            
            # Radar chart for quality ratings
            if response['analysis'].get('quality_ratings'):
                st.write("### 📊 Quality Ratings Breakdown")
                fig = create_radar_chart(response['analysis']['quality_ratings'], response['character_name'])
                st.plotly_chart(fig, use_container_width=True, 
                            key=f"char_radar_{response['character_id']}_{idx}_{response.get('created_at', '')}")
            
            # Detailed analysis
            with st.expander("📝 Detailed Analysis & Insights"):
                st.write(response['analysis'].get('analysis', ''))
            
            # User responses
            with st.expander("📋 Your Responses"):
                st.json(response['responses'])

    
    # Download report
    st.write("---")
    st.write("## 📥 Export Your Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Download JSON Report", use_container_width=True):
            import json
            report = {
                'user': username,
                'session_id': st.session_state.get('session_id'),
                'completed_assessments': len(responses),
                'average_rating': avg_rating,
                'strongest_archetype': highest_character['character_name'],
                'assessments': responses
            }
            st.download_button(
                label="💾 Download",
                data=json.dumps(report, indent=2),
                file_name=f"mahabharata_assessment_{st.session_state.get('session_id', 'report')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("🏠 Start New Assessment", use_container_width=True):
            st.switch_page("app.py")

def main():
    # Sidebar navigation
    with st.sidebar:
        st.title("🎭 Dashboard")
        
        st.write("---")
        
        # Show current user
        if 'username' in st.session_state:
            st.success(f"👤 Logged in as: **{st.session_state.username}**")
        
        view_mode = st.radio(
            "View Mode:",
            ["Current Session", "Past Sessions"],
            help="Switch between current session, history, or search other users"
        )
        
        st.write("---")
        st.write("### ℹ️ About")
        st.write("Explore your character assessments and discover insights from the Mahabharata.")
    
    # Main content based on view mode
    if view_mode == "Current Session":
        if 'session_id' not in st.session_state:
            st.error("⚠️ No active session found. Please complete the assessment first.")
            if st.button("Go to Assessment"):
                st.switch_page("app.py")
            return
        
        responses = load_session_data(st.session_state.session_id)
        display_dashboard(responses)
    
    elif view_mode == "Past Sessions":
        if 'username' not in st.session_state:
            st.error("⚠️ No user found. Please start an assessment first.")
            if st.button("Go to Assessment"):
                st.switch_page("app.py")
            return
        
        st.markdown("""
        <div class="dashboard-header">
            <h1>📚 Past Sessions History</h1>
            <p>Review your previous character assessments</p>
        </div>
        """, unsafe_allow_html=True)
        
        selected_session = display_session_list(st.session_state.username)
        
        if selected_session:
            st.write("---")
            responses = load_session_data(selected_session)
            display_dashboard(responses)
    
    else:  # Search by Username
        st.markdown("""
        <div class="dashboard-header">
            <h1>🔍 Search User Sessions</h1>
            <p>View any user's assessment history</p>
        </div>
        """, unsafe_allow_html=True)
        
        search_username = st.text_input(
            "🔎 Enter username to search:",
            placeholder="Enter exact username",
            help="Search for any user's assessment history"
        )
        
        if search_username:
            if st.button("Search", use_container_width=True):
                st.session_state.search_username = search_username
            
            if 'search_username' in st.session_state:
                db = Database()
                user = db.get_user_by_username(st.session_state.search_username)
                
                if user:
                    st.success(f"✅ Found user: **{user['username']}** (Joined: {user['created_at']})")
                    st.write("---")
                    
                    selected_session = display_session_list(st.session_state.search_username)
                    
                    if selected_session:
                        st.write("---")
                        responses = load_session_data(selected_session)
                        display_dashboard(responses)
                else:
                    st.error(f"❌ No user found with username: **{st.session_state.search_username}**")


if __name__ == "__main__":
    main()