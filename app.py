import streamlit as st
import json
from datetime import datetime
import uuid
from utils.database import Database
from utils.chatbot import CharacterChatbot
from dotenv import load_dotenv
import base64
load_dotenv()

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
    .passage-box {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    .analysis-box {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    .auth-box {
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 500px;
        margin: 0 auto;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        padding: 10px 25px;
        border: none;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.logged_in = False
    st.session_state.auth_mode = 'login'  # 'login' or 'signup'
    st.session_state.user_id = None
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.db = Database()
    st.session_state.chatbot = CharacterChatbot()
    st.session_state.current_character_idx = 0
    st.session_state.current_question_idx = 0
    st.session_state.responses = []
    st.session_state.read_passage = False
    st.session_state.stage = 'auth'  # auth, passage_choice, passage, questions, analysis
    st.session_state.rating_responses = {}
    st.session_state.username = None
    st.session_state.characters = st.session_state.chatbot.characters_data

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
        # st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        st.write("### 🔐 Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                else:
                    # Verify login
                    user = st.session_state.db.verify_user_login(username, password)
                    
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user['username']
                        st.session_state.user_id = user['id']
                        
                        # Create new session
                        st.session_state.session_id = str(uuid.uuid4())
                        st.session_state.db.create_session(st.session_state.session_id, st.session_state.user_id)
                        
                        st.session_state.stage = 'passage_choice'
                        st.session_state.initialized = True
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

def show_passage_choice():
    """Ask if user wants to read passage"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    
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
            st.rerun()

def show_passage():
    """Display character passage"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    
    st.markdown(f'<p class="character-title">{current_char["character"]}</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown(f"""
        <div class="passage-box">
            <h3>📖 The Story of {current_char['character']}</h3>
            <p style="text-align: justify; line-height: 1.8;">{current_char['passage']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("Continue to Questions ➡️", use_container_width=True):
        st.session_state.stage = 'questions'
        st.rerun()

def show_questions():
    """Display questions one by one"""
    current_char = st.session_state.characters[st.session_state.current_character_idx]
    questions = current_char['questions']
    
    if st.session_state.current_question_idx >= len(questions):
        submit_responses()
        return
    
    question = questions[st.session_state.current_question_idx]
    
    st.markdown(f'<p class="character-title">{current_char["character"]}</p>', unsafe_allow_html=True)
    st.progress((st.session_state.current_question_idx + 1) / len(questions))
    st.write(f"**Question {st.session_state.current_question_idx + 1} of {len(questions)}**")
    
    st.write(f"### {question['question']}")
    
    if question.get('rate_question'):
        st.write("**Rate yourself on the following qualities (1-5):**")
        st.write("*1 = Lowest, 5 = Highest*")
        
        ratings = {}
        for i, option in enumerate(question['options']):
            rating = st.slider(
                option,
                min_value=1,
                max_value=5,
                value=3,
                key=f"rating_{st.session_state.current_question_idx}_{i}"
            )
            ratings[option] = rating
        
        if st.button("Submit Ratings ➡️", use_container_width=True):
            st.session_state.responses.append(ratings)
            st.session_state.current_question_idx += 1
            st.rerun()
    else:
        with st.form(key=f"question_form_{st.session_state.current_question_idx}"):
            answer = st.text_area("Your Answer:", height=150, key=f"answer_{st.session_state.current_question_idx}")
            submitted = st.form_submit_button("Submit Answer ➡️", use_container_width=True)
            
            if submitted:
                if answer.strip():
                    st.session_state.responses.append(answer)
                    st.session_state.current_question_idx += 1
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
            st.write(f"- {strength}")
        
        st.write("### 💡 Recommendations")
        for rec in analysis.get('recommendations', []):
            st.write(f"- {rec}")
    
    with col2:
        st.write("### 🎯 Areas for Improvement")
        for area in analysis.get('areas_for_improvement', []):
            st.write(f"- {area}")
        
        st.write("### 🔍 Key Insights")
        for insight in analysis.get('key_insights', []):
            st.write(f"- {insight}")
    
    with st.expander("📝 Detailed Analysis"):
        st.write(analysis.get('analysis', ''))
    
    st.write("---")
    
    if st.session_state.current_character_idx < len(st.session_state.characters) - 1:
        if st.button("Next Character ➡️", use_container_width=True):
            st.session_state.current_character_idx += 1
            st.session_state.current_question_idx = 0
            st.session_state.responses = []
            st.session_state.read_passage = False
            st.session_state.stage = 'passage_choice'
            st.rerun()
    else:
        st.success("🎉 Congratulations! You have completed all character assessments!")
        st.info(f"📊 View your complete analysis in the Dashboard (sidebar)")
        
        if st.button("View Dashboard 📊", use_container_width=True):
            st.switch_page("pages/dashboard.py")

def main():
    """Main app logic"""
    
    # Sidebar
    with st.sidebar:
        st.image("assets/Mahabharat Krishna Wallpaper Teahub Io.jpg", width=100)
        st.title("🎭 Character Assessment")
        
        if st.session_state.logged_in:
            st.success(f"👤 **{st.session_state.username}**")
            
            if st.session_state.stage != 'auth':
                st.write(f"📍 **Character:** {st.session_state.current_character_idx + 1}/{len(st.session_state.characters)}")
                
                current_char = st.session_state.characters[st.session_state.current_character_idx]
                st.write(f"🎯 **{current_char['character']}**")
                
                st.write("---")
                st.write("### 📊 Progress")
                progress = st.session_state.current_character_idx / len(st.session_state.characters)
                st.progress(progress)
            
            st.write("---")
            if st.button("🚪 Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        st.write("---")
        st.write("### ℹ️ About")
        st.write("Discover your professional archetype based on Mahabharata characters.")
    
    # Main content
    if not st.session_state.logged_in:
        show_auth()
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