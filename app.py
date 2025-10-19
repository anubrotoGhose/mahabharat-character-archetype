# app.py
import streamlit as st
import json
from datetime import datetime
import time
import uuid
from utils.database import Database
from utils.chatbot import CharacterChatbot
from utils.pdf_generator import generate_analysis_report
from utils.pdf_generator import generate_completion_certificate 
import extra_streamlit_components as stx
from dotenv import load_dotenv
import base64
from pathlib import Path
load_dotenv()

# Add this helper function after imports
def get_character_image(image_path):
    """Convert character image to base64, return None if not found"""
    try:
        if Path(image_path).exists():
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error loading image: {e}")
    return None


def get_cookie_manager():
    return stx.CookieManager()

if 'cookie_manager' not in st.session_state:
    st.session_state.cookie_manager = get_cookie_manager()

cookie_manager = st.session_state.cookie_manager

# Function to save login state to cookies
def save_login_to_cookie(user_id, username):
    """Save user login information to cookies"""
    user_data = {
        'user_id': user_id,
        'username': username,
        'logged_in': True
    }
    cookie_manager.set('user_session', json.dumps(user_data), max_age=7*24*60*60)  # 7 days
    time.sleep(1)  # Important: Give time for cookie to be set

def load_login_from_cookie():
    """Load user login information from cookies"""
    user_cookie = cookie_manager.get('user_session')
    if user_cookie:
        try:
            user_data = json.loads(user_cookie)
            if user_data.get('logged_in'):
                return user_data
        except:
            pass
    return None

def clear_login_cookie():
    """Clear user session cookie"""
    try:
        cookie_manager.delete('user_session')
        time.sleep(1)
    except Exception as e:
        print(f"Error clearing cookie: {e}")

# Page configuration
st.set_page_config(
    page_title="Mahabharata Character Assessment Chatbot",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Dark mode detection and variables */
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #0e1117;
            --text-color: #fafafa;
            --border-color: #262730;
            --card-background: #262730;
            --passage-background: #1e2129;
        }
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --background-color: white;
            --text-color: #262730;
            --border-color: #e0e0e0;
            --card-background: white;
            --passage-background: #fff3cd;
        }
    }
    
    /* Apply to existing classes */
    .passage-box {
        background: var(--passage-background) !important;
        border-left: 5px solid #ffc107;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    
    .passage-box h3 {
        color: #ffc107 !important;
    }
    
    .passage-box p {
        color: var(--text-color) !important;
        text-align: justify;
        line-height: 1.8;
    }
    
    .analysis-box {
        background: var(--card-background) !important;
        border-left: 5px solid #28a745;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    
    .analysis-box h2, .analysis-box h3 {
        color: #28a745 !important;
    }
    
    .analysis-box p {
        color: var(--text-color) !important;
    }
    
    .auth-box {
        background: var(--card-background) !important;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 500px;
        margin: 0 auto;
        border: 1px solid var(--border-color);
    }
    
    .auth-box p, .auth-box h3 {
        color: var(--text-color) !important;
    }
    
    /* Main header stays the same (gradient) */
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .character-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 28px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        padding: 10px 25px;
        border: none;
        font-weight: bold;
    }
    
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    
    st.session_state.db = Database()
    st.session_state.chatbot = CharacterChatbot()
    
    saved_session = load_login_from_cookie()
    
    st.session_state.initialized = False
    st.session_state.logged_in = False
    st.session_state.auth_mode = 'login'  # 'login' or 'signup'
    st.session_state.user_id = None
    st.session_state.username = None
    
    # Restore from cookie if available
    if saved_session:
        st.session_state.logged_in = True
        st.session_state.user_id = saved_session['user_id']
        st.session_state.username = saved_session['username']
        st.session_state.stage = 'welcome'
    else:
        st.session_state.stage = 'auth'
    
    st.session_state.session_id = str(uuid.uuid4())
    
    st.session_state.current_character_idx = 0
    st.session_state.current_question_idx = 0
    st.session_state.responses = []
    st.session_state.read_passage = False
    st.session_state.stage = 'auth'  # auth, welcome, passage_choice, passage, questions, analysis
    st.session_state.rating_responses = {}
    
    st.session_state.characters = st.session_state.chatbot.characters_data
    
    st.session_state.question_flow = []
    st.session_state.current_question_data = None
    st.session_state.base_question_idx = 0

def show_auth():
    """Show login/signup screen"""
    st.markdown("""
        <style>
            .main-header {
                text-align: center;
                margin-top: 20px;
            }

            .main-header h1 {
                font-size: 2.5rem;
                line-height: 1.2;
                margin-bottom: 0.5rem;
                word-wrap: break-word;
            }

            .main-header p {
                font-size: 1.1rem;
                color: #555;
            }

            /* Mobile view: split line after 'Mahabharata And You' */
            @media (max-width: 600px) {
                .main-header h1 {
                    font-size: 1.8rem;
                }
                .main-header h1::after {
                    content: "\\A";      /* Add a line break */
                    white-space: pre;
                }
            }
        </style>

        <div class="main-header">
            <h1>'Mahabharata And You' Self Assessment</h1>
            <p style="color: white;">Discover Your Self For Career Excellence Through</p>
        </div>
    """,
    unsafe_allow_html=True
    )
    with open("assets/Mahabharat_And_You_Wallpapaer.jpeg", "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/jpeg;base64,{img_base64}" width="600" height="400" alt="Mahabharat and You">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.caption("")
    
    # Toggle between login and signup
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login", use_container_width=True, type="primary" if st.session_state.auth_mode == 'login' else "secondary"):
            st.session_state.auth_mode = 'login'
            st.rerun()
    with col2:
        if st.button("📝 Sign Up", use_container_width=True, type="primary" if st.session_state.auth_mode == 'signup' else "secondary"):
            st.session_state.auth_mode = 'signup'
            st.rerun()
    
    st.write("")
    
    if st.session_state.auth_mode == 'login':
        show_login()
    else:
        show_signup()

def show_login():
    """Show login form"""
    with st.container():
        st.write("### 🔐 Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me", value=True)
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                else:
                    user = st.session_state.db.verify_user_login(username, password)
                    
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user['username']
                        st.session_state.user_id = user['id']
                        st.session_state.stage = 'welcome'
                        st.session_state.initialized = True
                        
                        # Save to cookie if remember me is checked
                        if remember_me:
                            save_login_to_cookie(user['id'], user['username'])
                        
                        st.success(f"✅ Welcome back, {username}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_signup():
    """Show signup form"""
    with st.container():
        st.write("### 📝 Create New Account")
        
        with st.form("signup_form"):
            username = st.text_input("👤 Username", placeholder="Choose a unique username")
            password = st.text_input("🔒 Password", type="password", placeholder="Create a password")
            password_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter your password")
            
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submitted:
                if not username or not password or not password_confirm:
                    st.error("❌ Please fill in all fields")
                elif password != password_confirm:
                    st.error("❌ Passwords do not match")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters long")
                else:
                    # Check if username exists
                    if st.session_state.db.check_username_exists(username):
                        st.error(f"❌ Username '{username}' is already taken. Please choose another.")
                    else:
                        # Create new user
                        user_id = str(uuid.uuid4())
                        result = st.session_state.db.create_user_with_password(user_id, username, password)
                        
                        if result:
                            st.success(f"✅ Account created successfully! Welcome, {username}!")
                            st.info("🔐 Please login with your credentials")
                            st.session_state.auth_mode = 'login'
                            st.rerun()
                        else:
                            st.error("❌ Error creating account. Please try again.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
def show_welcome():
    """Show welcome screen with preview and options"""
    st.markdown(f"""
    <div class="main-header">
        <h1>Welcome, {st.session_state.username}! 🙏</h1>
        <p style="color: white;">Your journey through the Mahabharata awaits</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Preview text
    st.markdown("""
    <div style="background: var(--background-color, white); 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                margin: 20px 0;
                border: 1px solid var(--border-color, #e0e0e0);">
        <h3 style="color: #667eea; text-align: center;">📖 About This Assessment</h3>
        <p style="text-align: justify; 
                  line-height: 1.8; 
                  font-size: 16px;
                  color: var(--text-color, #262730);">
        Mahabharata, management and you, read by the author Amitrajit Ghosh, HR Professional and Executive Coach. 
        Mahabharata is the ultimate Indian epic which has remarkably portrayed all human traits ranging from desire 
        to sacrifice, jealousy to broad-minded, cruelty to compassion and short-sightedness to visionary. In order 
        to help the audience clearly distinguish between each of these traits, a character has been assigned to depict 
        a specific trait. And above all there is an ultimate supreme figure in the form of the great Krishna, who 
        symbolizes a Sampoonapurush or the complete man.
        </p>
        <p style="text-align: justify; 
                  line-height: 1.8; 
                  font-size: 16px;
                  color: var(--text-color, #262730);">
        The epic is over 5,000 years old, but even today in every walk of life we can see the story repeating itself 
        with only characters changing. In order to succeed in India, global business corporations and its executives 
        need to understand the history and culture of that nation. This book will give a deep insight into India's culture.
        </p>
        <p style="text-align: justify; 
                  line-height: 1.8; 
                  font-size: 16px;
                  color: var(--text-color, #262730);">
        In the subsequent chapters, let's understand the characters of Arjuna, Duryodhana, Dronacharya, Karna, Draupadi 
        and Krishna better and the learnings thereof, which in turn will help us in our career-building in organizations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Start New Assessment", use_container_width=True, type="primary"):
            # Create new session
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.db.create_session(st.session_state.session_id, st.session_state.user_id)
            st.session_state.current_character_idx = 0
            st.session_state.current_question_idx = 0
            st.session_state.responses = []
            st.session_state.read_passage = False
            st.session_state.stage = 'passage_choice'
            st.rerun()
    
    with col2:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("pages/dashboard.py")


# Update show_passage_choice function
def show_passage_choice():
    """Ask if user wants to read passage with character image"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    
    # Try to load character image
    char_image = get_character_image(current_char.get('image', ''))
    
    if char_image:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/jpeg;base64,{char_image}" 
                 style="border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 400px; width: 100%;"
                 alt="{current_char['character']}">
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<p class="character-title">{current_char["character"]}</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="character-title">Character: {current_char["character"]}</p>', unsafe_allow_html=True)
    
    st.write(f"Would you like to read the passage about **{current_char['character']}**?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, show me", use_container_width=True):
            st.session_state.read_passage = True
            st.session_state.stage = 'passage'
            st.rerun()
    with col2:
        if st.button("⏭️ No, skip to questions", use_container_width=True):
            st.session_state.read_passage = False
            st.session_state.stage = 'questions'
            # Initialize question flow
            st.session_state.question_flow = []
            st.session_state.current_question_data = current_char['questions'][0]
            st.session_state.base_question_idx = 0
            st.rerun()

def show_passage():
    """Display character passage with image"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    
    # Try to load character image
    char_image = get_character_image(current_char.get('image', ''))
    
    if char_image:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/jpeg;base64,{char_image}" 
                 style="border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 300px; width: 100%;"
                 alt="{current_char['character']}">
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f'<p class="character-title">{current_char["character"]}</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown(f"""
        <div class="passage-box">
            <h3>📖 About {current_char['character']}</h3>
            <p style="text-align: justify; line-height: 1.8;">{current_char['passage']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("Continue to Questions ➡️", use_container_width=True):
        st.session_state.stage = 'questions'
        # Initialize question flow
        st.session_state.question_flow = []
        st.session_state.current_question_data = current_char['questions'][0]
        st.session_state.base_question_idx = 0
        st.rerun()
        
def show_questions():
    """Display questions with dynamic follow-ups based on LLM"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    questions = current_char['questions']
    
    # Initialize question tracking if not exists
    if 'question_flow' not in st.session_state:
        st.session_state.question_flow = []
        st.session_state.current_question_data = questions[0]
        st.session_state.base_question_idx = 0
    
    current_question = st.session_state.current_question_data
    
    # Check if we've completed all questions
    if current_question is None:
        submit_responses()
        return
    
    st.markdown(f'<p class="character-title">{current_char["character"]}</p>', unsafe_allow_html=True)
    
    # Progress based on base questions (not follow-ups)
    total_base_questions = len(questions)
    completed_base = st.session_state.base_question_idx
    st.progress((completed_base + 1) / total_base_questions)
    st.write(f"**Question {completed_base + 1} of {total_base_questions}**")
    
    # Show if this is a follow-up question
    if current_question.get('is_follow_up'):
        st.info("📌 Follow-up question based on your previous answer")
    
    # Show guidance if available
    if current_question.get('guidance'):
        with st.expander("💡 Guidance"):
            st.write(current_question['guidance'])
    
    st.write(f"### {current_question['question']}")
    
    if current_question.get('rate_question'):
        st.write("**Rate yourself on the following qualities (0-10):**")
        st.write("*0 = Lowest, 10 = Highest*")
        
        ratings = {}
        for i, option in enumerate(current_question['options']):
            rating = st.slider(
                option,
                min_value=0,
                max_value=10,
                value=5,
                key=f"rating_{current_question['question_no']}_{i}"
            )
            ratings[option] = rating
        
        if st.button("Submit Ratings ➡️", use_container_width=True):
            # Store response with question metadata
            st.session_state.responses.append({
                'question_no': current_question['question_no'],
                'question': current_question['question'],
                'answer': ratings,
                'type': 'rating'
            })
            
            # Get next question using LLM orchestration
            next_question = st.session_state.chatbot.get_next_question(
                current_question,
                str(ratings),
                questions,
                st.session_state.base_question_idx
            )
            
            if next_question:
                st.session_state.current_question_data = next_question
                if not next_question.get('is_follow_up'):
                    st.session_state.base_question_idx += 1
            else:
                st.session_state.current_question_data = None
            
            st.rerun()
    else:
        with st.form(key=f"question_form_{current_question['question_no']}"):
            answer = st.text_area(
                "Your Answer:", 
                height=150, 
                key=f"answer_{current_question['question_no']}",
                placeholder="Please provide a detailed answer..."
            )
            submitted = st.form_submit_button("Submit Answer ➡️", use_container_width=True)
            
            if submitted:
                if answer.strip():
                    # Store response with metadata
                    st.session_state.responses.append({
                        'question_no': current_question['question_no'],
                        'question': current_question['question'],
                        'answer': answer,
                        'type': 'text'
                    })
                    
                    # Get next question using LLM orchestration
                    next_question = st.session_state.chatbot.get_next_question(
                        current_question,
                        answer,
                        questions,
                        st.session_state.base_question_idx
                    )
                    
                    if next_question:
                        st.session_state.current_question_data = next_question
                        if not next_question.get('is_follow_up'):
                            st.session_state.base_question_idx += 1
                    else:
                        st.session_state.current_question_data = None
                    
                    st.rerun()
                else:
                    st.warning("Please provide an answer before continuing.")

def submit_responses():
    """Submit responses and get analysis"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    
    with st.spinner("🔮 Analyzing your responses... This may take a moment..."):
        analysis = st.session_state.chatbot.analyze_responses(
            current_char['character'],
            current_char['passage'],
            current_char['questions'],
            st.session_state.responses
        )
        
        st.session_state.db.save_character_response(
            st.session_state.session_id,
            current_char['id'],
            current_char['character'],
            st.session_state.read_passage,
            st.session_state.responses,
            analysis
        )
        
        st.session_state.current_analysis = analysis
        st.session_state.stage = 'analysis'
        st.rerun()


def show_analysis():
    """Display analysis results"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    analysis = st.session_state.current_analysis
    
    # Display character image if available
    char_image = get_character_image(current_char.get('image', ''))
    
    if char_image:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/jpeg;base64,{char_image}" 
                 style="border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 250px; width: 100%;"
                 alt="{current_char['character']}">
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f'<p class="character-title">{current_char["character"]} - Assessment Complete!</p>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="analysis-box">
        <h2>📊 Your Analysis</h2>
        <h3 style="color: #667eea;">Overall Rating: {analysis['overall_rating']}/10</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 💪 Strengths")
        for strength in analysis.get('strengths', []):
            st.write(f"✓ {strength}")
        
        st.write("### 💡 Recommendations")
        for rec in analysis.get('recommendations', []):
            st.write(f"→ {rec}")
    
    with col2:
        st.write("### 🎯 Areas for Improvement")
        for area in analysis.get('areas_for_improvement', []):
            st.write(f"○ {area}")
        
        st.write("### 🔍 Key Insights")
        for insight in analysis.get('key_insights', []):
            st.write(f"• {insight}")
    
    with st.expander("📝 Detailed Analysis"):
        st.write(analysis.get('analysis', ''))
    
    st.write("---")
    
    # Check if there are more characters
    if st.session_state.current_character_idx < len(st.session_state.characters) - 1:
        if st.button("Next Character ➡️", use_container_width=True):
            # Reset for next character
            st.session_state.current_character_idx += 1
            st.session_state.current_question_idx = 0
            st.session_state.responses = []
            st.session_state.read_passage = False
            st.session_state.question_flow = []
            st.session_state.current_question_data = None
            st.session_state.base_question_idx = 0
            st.session_state.stage = 'passage_choice'
            st.rerun()
    else:
        # All characters completed
        st.success("🎉 Congratulations! You have completed all character assessments!")
        st.info(f"📊 View your complete analysis in the Dashboard")
        
        # PDF DOWNLOADS SECTION
        st.write("---")
        st.write("## 📥 Download Your Documents")
        
        # Get all session responses for PDF generation
        db = Database()
        all_responses = db.get_session_responses(st.session_state.session_id)
        
        if all_responses:
            avg_rating = sum([r['analysis']['overall_rating'] for r in all_responses]) / len(all_responses)
            highest_character = max(all_responses, key=lambda x: x['analysis']['overall_rating'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Generate completion certificate                
                cert_pdf = generate_completion_certificate(
                    username=st.session_state.username,
                    session_id=st.session_state.session_id,
                    completion_date=datetime.now().strftime('%B %d, %Y'),
                    total_characters=len(all_responses)
                )
                
                st.download_button(
                    label="📜 Download Completion Certificate",
                    data=cert_pdf,
                    file_name=f"Certificate_{st.session_state.username}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col2:
                # Generate analysis report                
                report_pdf = generate_analysis_report(
                    username=st.session_state.username,
                    session_id=st.session_state.session_id,
                    responses=all_responses,
                    avg_rating=avg_rating,
                    strongest_character=highest_character['character_name']
                )
                
                st.download_button(
                    label="📊 Download Analysis Report",
                    data=report_pdf,
                    file_name=f"Analysis_Report_{st.session_state.username}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        st.write("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 View Dashboard", use_container_width=True, type="primary"):
                st.switch_page("pages/dashboard.py")
        
        with col2:
            if st.button("🏠 Go Home", use_container_width=True):
                st.session_state.stage = 'welcome'
                st.rerun()

def main():
    """Main app logic"""
    
    # Sidebar
    with st.sidebar:
        st.image("assets/Mahabharat Krishna Wallpaper Teahub Io.jpg", width=100)
        
        # ADD CUSTOM NAVIGATION HERE
        if st.session_state.logged_in:
            st.write("### 🧭 Navigation")
            if st.button("🏠 Main", use_container_width=True, type="secondary" if st.session_state.stage == 'welcome' else "primary"):
                st.session_state.stage = 'welcome'
                st.rerun()
            
            if st.button("📊 Dashboard", use_container_width=True):
                st.switch_page("pages/dashboard.py")
        
        st.write("---")
        
        if st.session_state.logged_in:
            st.success(f"👤 **{st.session_state.username}**")
            
            if st.session_state.stage not in ['auth', 'welcome']:
                st.write(f"📍 **Character:** {st.session_state.current_character_idx + 1}/{len(st.session_state.characters)}")
                
                current_char = st.session_state.characters[st.session_state.current_character_idx]
                st.write(f"🎯 **{current_char['character']}**")
                
                st.write("---")
                st.write("### 📊 Progress")
                progress = st.session_state.current_character_idx / len(st.session_state.characters)
                st.progress(progress)
            
            st.write("---")
            if st.button("🚪 Logout"):
                clear_login_cookie()  # Clear the cookie
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        st.write("---")
        st.write("### ℹ️ About")
        st.write("Discover your professional archetype based on Mahabharata characters.")
    
    # Main content
    if not st.session_state.logged_in:
        show_auth()
    elif st.session_state.stage == 'welcome':
        show_welcome()
    elif st.session_state.stage == 'passage_choice':
        show_passage_choice()
    elif st.session_state.stage == 'passage':
        show_passage()
    elif st.session_state.stage == 'questions':
        show_questions()
    elif st.session_state.stage == 'analysis':
        show_analysis()


if __name__ == "__main__":
    main()