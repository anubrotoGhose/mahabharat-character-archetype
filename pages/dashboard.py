# pages/dashboard.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.database import Database
from datetime import datetime
from utils.pdf_generator import generate_analysis_report
from utils.pdf_generator import generate_completion_certificate   
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

# Hide default Streamlit navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("🔒 **Access Denied**: You must be logged in to view the dashboard.")
    st.info("👉 Please go to the home page and login first.")
    
    if st.button("🏠 Go to Login Page", use_container_width=True):
        st.switch_page("app.py")
    
    st.stop()  # Stop execution here if not logged in   


def datetime_handler(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


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
            total_chars = 6  # Total number of characters
            is_complete = session['completed'] >= total_chars
            has_data = session['completed'] > 0
            
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                # Add completion badge
                badge = "✅ Complete" if is_complete else "🔄 In Progress" if has_data else "📝 New"
                badge_color = "#28a745" if is_complete else "#ffc107" if has_data else "#6c757d"
                
                st.markdown(f"""
                <div class="session-card">
                    <h4>📝 Session #{idx + 1} <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; margin-left: 8px;">{badge}</span></h4>
                    <p style="font-size: 12px; color: #666;">ID: {session['id'][:12]}...</p>
                    <p>📅 {session['created_at']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.write(f"**{session['completed']}/{total_chars}** characters completed")
                completion_pct = (session['completed'] / total_chars) * 100
                st.progress(min(completion_pct / 100, 1.0))
            
            with col3:
                # View button - only enabled if there's data
                if has_data:
                    if st.button("👁️ View", key=f"view_{session['id']}", use_container_width=True):
                        selected_session = session['id']
                        st.session_state.selected_session = selected_session
                else:
                    st.button("👁️ View", key=f"view_{session['id']}", use_container_width=True, disabled=True)
                    st.caption("No data")
            
            with col4:
                # Continue button - only for incomplete sessions
                if not is_complete:
                    if st.button("▶️ Continue", key=f"continue_{session['id']}", use_container_width=True, type="primary"):
                        # Load this session and continue from where they left off
                        st.session_state.session_id = session['id']
                        st.session_state.current_character_idx = session['completed']  # Start from next character
                        st.session_state.current_question_idx = 0
                        st.session_state.responses = []
                        st.session_state.read_passage = False
                        st.session_state.question_flow = []
                        st.session_state.current_question_data = None
                        st.session_state.base_question_idx = 0
                        st.session_state.stage = 'passage_choice'
                        
                        # Switch to main app
                        st.switch_page("app.py")
                else:
                    # Show a checkmark for completed sessions
                    st.markdown("✅", help="Completed")
            
            with col5:
                # Delete button
                if st.button("🗑️", key=f"delete_{session['id']}", use_container_width=True, help="Delete this session"):
                    # Add confirmation
                    if f"confirm_delete_{session['id']}" not in st.session_state:
                        st.session_state[f"confirm_delete_{session['id']}"] = True
                        st.warning("⚠️ Click delete again to confirm")
                        st.rerun()
                    else:
                        db = Database()
                        if db.delete_session(session['id']):
                            del st.session_state[f"confirm_delete_{session['id']}"]
                            st.success("Session deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")
    
    return selected_session


def display_dashboard(responses, session_info=None):
    """Display complete dashboard for a session"""
    
    # Header with Krishna-Arjuna theme
    # Get username from session state or session_info
    username = st.session_state.get('username')
    if not username and session_info:
        username = session_info.get('username', 'User')
    if not username:
        username = 'User'
            
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>🎭 Character Assessment Dashboard</h1>
        <p style="font-size: 18px;">Welcome, {username}!</p>
        <p>Discover your inner strength through the wisdom of Mahabharata</p>
        <p style="font-size: 14px; opacity: 0.9;">✨ "योगः कर्मसु कौशलम्" - Excellence in action is Yoga ✨</p>
    </div>
    """, unsafe_allow_html=True)
    
    summary_image = get_base64_image('assets/Final_Summary.jpeg')
    
    if summary_image:
        st.markdown(
            f'''
            <div style="text-align: center;">
                <img src="data:image/jpeg;base64,{summary_image}" alt="Dashboard Summary" style="max-width: 600px; width: 100%; border-radius: 18px; margin: 20px 0; box-shadow: 0 4px 24px rgba(25,0,70,.15);"/>
            </div>
            ''', unsafe_allow_html=True
        )
    
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

    # Download section
    st.write("---")
    st.write("## 📥 Export Your Results")
    
    # Determine if all 6 characters are completed for certificate
    is_complete = len(responses) >= 6
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
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
            label="📄 Download JSON Report",
            data=json.dumps(report, indent=2, default=datetime_handler),
            file_name=f"mahabharata_assessment_{st.session_state.get('session_id', 'report')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # PDF Analysis Report - Always available if there's data
        
        # Get session_id from responses or session_state
        session_id = responses[0].get('session_id', st.session_state.get('session_id', 'unknown'))
        
        report_pdf = generate_analysis_report(
            username=username,
            session_id=session_id,
            responses=responses,
            avg_rating=avg_rating,
            strongest_character=highest_character['character_name']
        )
        
        st.download_button(
            label="📊 Download Analysis Report (PDF)",
            data=report_pdf,
            file_name=f"Analysis_Report_{username}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col3:
        # Completion Certificate - Only if all 6 completed
        if is_complete:
            
            # Get completion date from last response
            completion_date = responses[-1].get('created_at', datetime.now().strftime('%B %d, %Y'))
            if isinstance(completion_date, str) and '-' in completion_date:
                # Convert from database format to readable format
                try:
                    from datetime import datetime as dt
                    completion_date = dt.strptime(completion_date.split()[0], '%Y-%m-%d').strftime('%B %d, %Y')
                except:
                    completion_date = datetime.now().strftime('%B %d, %Y')
            
            cert_pdf = generate_completion_certificate(
                username=username,
                session_id=session_id,
                completion_date=completion_date,
                total_characters=len(responses)
            )
            
            st.download_button(
                label="📜 Download Certificate (PDF)",
                data=cert_pdf,
                file_name=f"Certificate_{username}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info(f"🏆 Complete all 6 characters to unlock your certificate!\n\n({len(responses)}/6 completed)")
    
    st.write("---")
    
    # Start new assessment button
    if st.button("🏠 Start New Assessment", use_container_width=True):
        st.switch_page("app.py")

def main():
    # Sidebar navigation - SAME AS APP.PY
    with st.sidebar:
        st.image("assets/Mahabharat Krishna Wallpaper Teahub Io.jpg", width=100)
        
        # CUSTOM NAVIGATION
        if st.session_state.logged_in:
            st.write("### 🧭 Navigation")
            if st.button("🏠 Main", use_container_width=True):
                st.switch_page("app.py")
            
            if st.button("📊 Dashboard", use_container_width=True, type="primary"):
                st.rerun()
        
        st.write("---")
        
        if st.session_state.logged_in:
            st.success(f"👤 **{st.session_state.username}**")
            
            # Show view mode selector
            view_mode = st.radio(
                "📂 View Mode:",
                ["Current Session", "Past Sessions"],
                help="Switch between current session and history"
            )
            
            st.session_state.dashboard_view_mode = view_mode
            
            st.write("---")
            
            # Logout button
            from app import clear_login_cookie  # Import from app.py
            if st.button("🚪 Logout", use_container_width=True):
                clear_login_cookie()
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.switch_page("app.py")
        
        st.write("---")
        st.write("### ℹ️ About")
        st.write("Explore your character assessments and discover insights from the Mahabharata.")
    
    # Get view mode from session state (default to "Current Session")
    view_mode = st.session_state.get('dashboard_view_mode', 'Current Session')
    
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



if __name__ == "__main__":
    main()