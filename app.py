import streamlit as st
import database as db
import extra_streamlit_components as stx
import datetime
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Change Makers 8c", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

# --- HIDE STREAMLIT BRANDING & MENU ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden; display: none;}
            .stDeployButton {display:none !important;}
            button[title="Collapse sidebar"] {display: none !important;}
            button[title="Expand sidebar"] {display: none !important;}
            [data-testid="collapsedControl"] {display: none !important;}
            [data-testid="stSidebarCollapseButton"] {display: none !important;}
            [data-testid="stSidebarCollapseControl"] {display: none !important;}
            [data-testid="stSidebarHeader"] button {display: none !important;}
            [data-testid="stViewerBadge"] {display: none !important;}
            div[class^='viewerBadge'] {display: none !important;}
            div[class*='viewerBadge'] {display: none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)


# --- FIREBASE AUTHENTICATION SETUP ---
import os
auth = None
USE_FIREBASE_AUTH = False
firebase_setup_error = None

# Safely check if secrets exist at all
secrets_exist = False
try:
    _ = st.secrets
    secrets_exist = True
except Exception:
    pass

def get_secret(key):
    if secrets_exist and key in st.secrets:
        return st.secrets[key]
    return os.environ.get(key)

api_key = get_secret("firebase_api_key")
proj_id = get_secret("firebase_project_id")

try:
    if api_key and proj_id:
        import pyrebase
        config = {
            "apiKey": api_key,
            "authDomain": f"{proj_id}.firebaseapp.com",
            "projectId": proj_id,
            "databaseURL": "",
            "storageBucket": f"{proj_id}.appspot.com",
            "messagingSenderId": "",
            "appId": "",
            "measurementId": ""
        }
        firebase_app = pyrebase.initialize_app(config)
        auth = firebase_app.auth()
        USE_FIREBASE_AUTH = True
except Exception as e:
    firebase_setup_error = str(e)


# --- LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- COOKIE MANAGER (24 HR PERSISTENT LOGIN) ---
cookie_manager = stx.CookieManager()

stored_username = cookie_manager.get(cookie="cm_username")
if stored_username and not st.session_state.logged_in:
    st.session_state.logged_in = True
    st.session_state.username = stored_username
    st.rerun()

if not st.session_state.logged_in:
    # Use columns to center the login form and prevent it from stretching
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔒 Login Required")
        st.markdown("Please log in or create an account to access the Model Museum.")
        
        if USE_FIREBASE_AUTH:
            tab1, tab2 = st.tabs(["Login", "Create Account"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("Login"):
                        fake_email = f"{username.lower().replace(' ', '')}@changemakers.local"
                        try:
                            user = auth.sign_in_with_email_and_password(fake_email, password)
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            # Set cookie for 24 hours
                            cookie_manager.set("cm_username", username, expires_at=datetime.datetime.now() + datetime.timedelta(days=1))
                            import time; time.sleep(1) # Wait for cookie to save
                            st.rerun()
                        except Exception as e:
                            st.error("Invalid username or password.")
                            
            with tab2:
                with st.form("signup_form"):
                    new_username = st.text_input("Choose a Username")
                    new_password = st.text_input("Choose a Password (min 6 characters)", type="password")
                    if st.form_submit_button("Create Account"):
                        fake_email = f"{new_username.lower().replace(' ', '')}@changemakers.local"
                        try:
                            user = auth.create_user_with_email_and_password(fake_email, new_password)
                            st.success(f"Account '{new_username}' created successfully! Please log in on the other tab.")
                        except Exception as e:
                            st.error("Username might already be taken, or password is too short.")
        else:
            if firebase_setup_error:
                st.error(f"⚠️ Firebase Error: {firebase_setup_error}")
                
            if not secrets_exist:
                st.error("⚠️ No secrets file found. If you are running locally, create `.streamlit/secrets.toml`")
            elif "firebase_api_key" not in st.secrets or "firebase_project_id" not in st.secrets:
                st.error("⚠️ Missing `firebase_api_key` or `firebase_project_id` in secrets.")
                
            st.warning("Firebase Authentication is not configured yet. Falling back to simple admin password.")
            
            with st.form("simple_login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    correct_username = "admin"
                    correct_password = "changemakers"
                    if secrets_exist:
                        correct_username = st.secrets.get("admin_username", correct_username)
                        correct_password = st.secrets.get("admin_password", correct_password)
                    
                    if username == correct_username and password == correct_password:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        cookie_manager.set("cm_username", username, expires_at=datetime.datetime.now() + datetime.timedelta(days=1))
                        import time; time.sleep(1) # Wait for cookie to save
                        st.rerun()
                    else:
                        st.error("Incorrect username or password.")
                        
    st.stop()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🏛️ Museum Menu")
    
    page = option_menu(
        menu_title=None, 
        options=["Dashboard", "Add a Model", "My Profile", "Logout"], 
        icons=["house", "plus-square", "person-circle", "box-arrow-right"], 
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "orange", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#ff4b4b"},
        }
    )
    
    st.divider()
    st.markdown(f"**Logged in as:** {st.session_state.username}")

# --- ACTION: LOGOUT ---
if page == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = ""
    cookie_manager.delete("cm_username")
    st.rerun()

# --- PAGE: MY PROFILE ---
elif page == "My Profile":
    st.title("👤 My Profile")
    st.markdown(f"**Username:** {st.session_state.username}")
    st.info("In the future, you will be able to see all the models you've added right here!")

# --- PAGE: ADD A MODEL ---
elif page == "Add a Model":
    st.title("➕ Add a New Model")
    st.markdown("Fill out the details below to add a new model to the museum.")
    
    with st.form("add_model_form", clear_on_submit=True):
        title = st.text_input("Model Name", max_chars=100)
        desc = st.text_area("Description")
        img = st.file_uploader("Upload Image (Optional)", type=["jpg", "jpeg", "png", "webp"])
        
        submitted = st.form_submit_button("Add Model")
        if submitted:
            if title:
                with st.spinner("Uploading..."):
                    db.add_model(title, desc, img)
                st.success("Model added successfully! Switch to the Dashboard to see it.")
            else:
                st.error("Please provide at least a name for the model.")
    
# --- PAGE: DASHBOARD ---
elif page == "Dashboard":
    st.title("🏛️ Change Makers Model Museum")
    st.markdown("Welcome to the Model Museum! Explore our models below.")

    # --- MAIN CONTENT: GALLERY ---
    models = db.load_models()

    if not models:
        st.info("The museum is currently empty. Go to 'Add a Model' in the sidebar to be the first!")
    else:
        cols_per_row = 3
        for i in range(0, len(models), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(models):
                    m = models[i + j]
                    with col:
                        st.subheader(m.get("title", "Untitled"))
                        
                        if m.get("image_url"):
                            st.image(m["image_url"], use_container_width=True)
                        
                        if m.get("description"):
                            st.write(m["description"])
                            
                        # Edit / Delete Section
                        with st.expander("Edit / Delete"):
                            with st.form(f"edit_form_{m['id']}"):
                                edit_title = st.text_input("Name", value=m.get("title", ""))
                                edit_desc = st.text_area("Description", value=m.get("description", ""))
                                edit_img = st.file_uploader("New Image (optional)", type=["jpg", "jpeg", "png", "webp"])
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("Update"):
                                        with st.spinner("Updating..."):
                                            db.update_model(m["id"], edit_title, edit_desc, edit_img)
                                        st.success("Updated!")
                                        st.rerun()
                                with col2:
                                    if st.form_submit_button("Delete ❌"):
                                        db.delete_model(m["id"])
                                        st.rerun()
