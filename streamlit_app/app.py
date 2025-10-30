"""
LegalBot - Streamlit UI with Prisma + JWT Authentication
AI-Powered Judiciary Reference System
"""
import streamlit as st
import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend import auth_prisma, retrieval_prisma, llm_handler
from backend.async_helper import run_async

# Page configuration
st.set_page_config(
    page_title="LegalBot - AI Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4788;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .disclaimer {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .source-box {
        background-color: #fff4cc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff9800;
        margin: 0.5rem 0;
        color: #000000;
    }
    .source-box strong {
        color: #000000;
        font-weight: 700;
    }
    .source-box small {
        color: #1a1a1a;
        display: block;
        margin-top: 0.5rem;
        line-height: 1.5;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #000000;
    }
    .user-message {
        background-color: #cfe2ff;
        border-left: 5px solid #0d6efd;
    }
    .bot-message {
        background-color: #d1e7dd;
        border-left: 5px solid #198754;
    }
    .chat-message strong {
        color: #000000;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state - FIXED: Initialize each key separately
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'jwt_token' not in st.session_state:
    st.session_state.jwt_token = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def show_login_page():
    """Display login/signup page"""
    st.markdown("<h1 class='main-header'>⚖️ LegalBot</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>AI-Powered Judiciary Reference System</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login")

            if submit:
                if email and password:
                    with st.spinner("Authenticating..."):
                        try:
                            # FIXED: Use safe async wrapper
                            success, message, token, user_data = run_async(
                                auth_prisma.login_user(email, password)
                            )

                            if success:
                                st.session_state.logged_in = True
                                st.session_state.user = user_data
                                st.session_state.jwt_token = token
                                st.session_state.chat_history = []
                                st.success("✓ Logged in successfully!")
                                # Force rerun to show chat page
                                st.rerun()
                            else:
                                st.error(f"✗ {message}")
                        except Exception as e:
                            st.error(f"✗ Login error: {str(e)}")
                            st.info("💡 Tip: Check if database is configured correctly in .env")
                            with st.expander("See error details"):
                                st.code(str(e))
                else:
                    st.warning("Please enter both email and password")

    with tab2:
        st.subheader("Create New Account")
        with st.form("signup_form"):
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
            submit = st.form_submit_button("Sign Up")

            if submit:
                if name and email and password and password_confirm:
                    if password != password_confirm:
                        st.error("✗ Passwords do not match")
                    elif len(password) < 6:
                        st.error("✗ Password must be at least 6 characters")
                    else:
                        with st.spinner("Creating account..."):
                            try:
                                success, message, token = run_async(
                                    auth_prisma.signup_user(email, password, name)
                                )

                                if success:
                                    st.success("✓ Account created successfully! Please login.")
                                else:
                                    st.error(f"✗ {message}")
                            except Exception as e:
                                st.error(f"✗ Signup error: {str(e)}")
                                st.info("💡 Tip: Check if database is configured correctly in .env")
                                with st.expander("See error details"):
                                    st.code(str(e))
                else:
                    st.warning("Please fill in all fields")

def show_chat_page():
    """Display main chat interface"""

    # FIXED: Validate user session
    if not st.session_state.user:
        st.error("Session error. Please login again.")
        st.session_state.logged_in = False
        st.rerun()
        return

    user_name = st.session_state.user.get('name', 'User')

    # Sidebar
    with st.sidebar:
        st.title(f"👤 {user_name}")
        st.markdown("---")

        # Quick actions
        st.subheader("💡 Quick Questions")
        quick_questions = [
            "What is Section 302 IPC?",
            "Explain bail provisions in CrPC",
            "Cognizable vs non-cognizable offences?",
            "Rights of an arrested person?",
            "Defamation laws in India"
        ]

        for question in quick_questions:
            if st.button(question, key=f"quick_{hash(question)}"):
                st.session_state.current_query = question
                st.rerun()

        st.markdown("---")

        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.jwt_token = None
            st.session_state.chat_history = []
            st.rerun()

    # Main chat area
    st.markdown("<h1 class='main-header'>⚖️ LegalBot Assistant</h1>", unsafe_allow_html=True)
    st.markdown(f"**Welcome, {user_name}!** Ask me any legal questions.")

    # Display chat history
    for i, chat in enumerate(st.session_state.chat_history):
        # User message
        st.markdown(f"""
        <div class='chat-message user-message'>
            <strong>🧑 You:</strong><br>{chat['query']}
        </div>
        """, unsafe_allow_html=True)

        # Bot message
        st.markdown(f"""
        <div class='chat-message bot-message'>
            <strong>🤖 LegalBot:</strong><br>{chat['response']}
        </div>
        """, unsafe_allow_html=True)

        # Sources
        if chat.get('sources') and len(chat['sources']) > 0:
            with st.expander(f"📚 View Sources ({len(chat['sources'])} references)"):
                for j, source in enumerate(chat['sources']):
                    st.markdown(f"""
                    <div class='source-box'>
                        <strong>Source {j+1}:</strong> {source['document']} (Page {source['page']})<br>
                        <small>{source['text']}</small>
                    </div>
                    """, unsafe_allow_html=True)

        # Feedback
        col1, col2, col3 = st.columns([1, 1, 8])

        rating_status = chat.get('rating', None)

        with col1:
            if st.button("👍", key=f"up_{i}", disabled=(rating_status == 'positive')):
                chat['rating'] = 'positive'
                st.success("Thanks!")

        with col2:
            if st.button("👎", key=f"down_{i}", disabled=(rating_status == 'negative')):
                chat['rating'] = 'negative'
                st.info("Noted")

    # Input area
    st.markdown("---")

    # Check for quick question
    query = ""
    if 'current_query' in st.session_state:
        query = st.session_state.current_query
        del st.session_state.current_query

    # Query input
    user_query = st.text_input(
        "Ask your legal question:",
        value=query,
        placeholder="e.g., What is Section 420 IPC?",
        key="user_input"
    )

    col1, col2 = st.columns([6, 1])
    with col1:
        search_mode = st.radio(
            "Search Mode:",
            ["PDF + AI", "AI Only"],
            horizontal=True,
            help="PDF + AI: Search documents first, then use AI. AI Only: Direct AI response."
        )
    with col2:
        submit = st.button("🔍 Ask", type="primary")

    if submit and user_query:
        with st.spinner("🔍 Searching legal documents..."):
            try:
                sources = []

                if search_mode == "PDF + AI":
                    # Try retrieval from PDFs
                    if retrieval_prisma.check_index_exists():
                        # FIXED: Use run_async instead of asyncio.run to prevent event loop issues
                        results = run_async(retrieval_prisma.search(user_query, top_k=5))
                        context = retrieval_prisma.get_context_for_llm(results)
                        sources = retrieval_prisma.format_sources(results)

                        # Generate answer with LLM
                        response = llm_handler.generate_answer(user_query, context)
                    else:
                        st.warning("No documents indexed. Using AI-only mode.")
                        response = llm_handler.generate_quick_answer(user_query)
                else:
                    # AI only mode
                    response = llm_handler.generate_quick_answer(user_query)

                # Add to chat history FIRST (so user sees it immediately)
                chat_entry = {
                    "query": user_query,
                    "response": response,
                    "sources": sources
                }
                st.session_state.chat_history.append(chat_entry)

                # Rerun to display immediately
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("💡 Try using 'AI Only' mode or check your API configuration.")
                with st.expander("Error details"):
                    st.code(str(e))

def main():
    """Main application logic"""
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_chat_page()

if __name__ == "__main__":
    main()
