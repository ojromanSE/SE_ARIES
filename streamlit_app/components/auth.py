"""Simple session-based auth for Streamlit."""
import streamlit as st
from passlib.context import CryptContext
from services.db import get_db, User

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def login_form():
    """Render login form and return True if authenticated."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div style='text-align:center; padding: 2rem 0 1rem'>
        <h1 style='font-size:2rem; color:#0ea5e9'>⚡ SE_ARIES</h1>
        <p style='color:#9ca3af'>Petroleum Economics Platform</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Sign In")
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                db = get_db()
                try:
                    user = db.query(User).filter(User.username == username).first()
                    if user and pwd_ctx.verify(password, user.hashed_password) and user.is_active:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user.username
                        st.session_state["user_role"] = user.role
                        st.session_state["full_name"] = user.full_name or user.username
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                finally:
                    db.close()

        st.caption("Default: admin / admin123")
    return False


def logout():
    for key in ["authenticated", "username", "user_role", "full_name"]:
        st.session_state.pop(key, None)
    st.rerun()


def require_auth():
    """Call at top of each page to enforce authentication."""
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()
