import streamlit as st
import database as db

def login_user():
    """Simple login form."""
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            user = db.validate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"Welcome back, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def register_user():
    """Simple registration form."""
    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        name = st.text_input("Full Name")
        campus = st.selectbox("Campus", ["Harvey Mudd", "Scripps", "Pomona", "Claremont McKenna", "Pitzer"])
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if not (username and password and name and campus):
                st.error("All fields are required!")
                return
                
            user_id = db.create_user(username, password, name, campus)
            if user_id:
                st.error("Registration successful! Please log in.")
                st.session_state.show_login = True
                st.rerun()
            else:
                st.error("Username already exists!")

def logout_user():
    """Log out the current user."""
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def init_auth():
    """Initialize authentication state."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            login_user()
            
        with tab2:
            register_user()
            
        return False
    return True