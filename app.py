import streamlit as st
import database as db
import extra_streamlit_components as stx
import datetime
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Change Makers 8c", page_icon="", layout="wide", initial_sidebar_state="expanded")

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if st.session_state.theme == "Light":
    st.markdown("""
    <style>
        html { filter: invert(1) hue-rotate(180deg); }
        img, video, iframe, [data-testid="stImage"] { filter: invert(1) hue-rotate(180deg); }
    </style>
    """, unsafe_allow_html=True)


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

            [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
                height: 100%; min-height: calc(100vh - 8rem);
            }
            div.element-container:has(.bottom-spacer) {
                flex-grow: 1;
            }
            div.stButton > button {
                border-radius: 0px !important;
            }
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
if "role" not in st.session_state:
    if st.session_state.get("username"):
        st.session_state.role = db.get_user_role(st.session_state.username)
    else:
        st.session_state.role = "viewer"

# --- COOKIE MANAGER (24 HR PERSISTENT LOGIN) ---
cookie_manager = stx.CookieManager()

stored_username = cookie_manager.get(cookie="cm_username")

if stored_username and isinstance(stored_username, str) and not st.session_state.logged_in and not st.session_state.get("ignore_cookie", False):
    role = db.get_user_role(stored_username)
    if role != "banned":
        st.session_state.logged_in = True
        st.session_state.username = stored_username
        st.session_state.role = role
        st.rerun()

if not st.session_state.logged_in:
    # Use columns to center the login form and prevent it from stretching
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("Login Required")
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
                            st.session_state.ignore_cookie = False
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = db.get_user_role(username)
                            # Set cookie for 24 hours
                            cookie_manager.set("cm_username", username, expires_at=datetime.datetime.now() + datetime.timedelta(days=1))
                        except Exception as e:
                            try:
                                import json
                                error_json = e.args[1]
                                error_data = json.loads(error_json)
                                st.error(f"Login failed: {error_data['error']['message']}")
                            except:
                                st.error(f"Login failed: {str(e)}")
                            
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
                            try:
                                import json
                                error_json = e.args[1]
                                error_data = json.loads(error_json)
                                st.error(f"Error creating account: {error_data['error']['message']}")
                            except:
                                st.error(f"Error creating account: {str(e)}")
        else:
            if firebase_setup_error:
                st.error(f" Firebase Error: {firebase_setup_error}")
                
            if not secrets_exist:
                st.error("No secrets file found. If you are running locally, create `.streamlit/secrets.toml`")
            elif "firebase_api_key" not in st.secrets or "firebase_project_id" not in st.secrets:
                st.error("Missing `firebase_api_key` or `firebase_project_id` in secrets.")
                
            st.warning("Firebase Authentication is not configured yet. Falling back to simple admin password.")
            
            with st.form("simple_login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    correct_password = "changemakers"
                    if secrets_exist:
                        correct_password = st.secrets.get("admin_password", correct_password)
                    
                    if password == correct_password and len(username.strip()) > 0:
                        role = db.get_user_role(username.strip())
                        if role == "banned":
                            st.error("This account has been banned by an administrator.")
                        else:
                            st.session_state.ignore_cookie = False
                            st.session_state.logged_in = True
                            st.session_state.username = username.strip()
                            st.session_state.role = role
                            cookie_manager.set("cm_username", username.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(days=1))
                    else:
                        st.error("Incorrect username or password.")
                        
    if not st.session_state.logged_in:
        st.stop()
    else:
        st.rerun()

# --- SIDEBAR NAVIGATION ---
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

with st.sidebar:
    st.title("Museum Menu")
    if st.button("Dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"
    action_name = "Add a Model" if st.session_state.role == "super_admin" else "Send a Model"
    if st.button(action_name, use_container_width=True):
        st.session_state.page = action_name
        
    if st.session_state.role == "super_admin":
        if st.button("Approve a Model", use_container_width=True):
            st.session_state.page = "Approve a Model"
        if st.button("Super Admin Settings", use_container_width=True):
            st.session_state.page = "Super Admin"
            
    st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)
    
    # Profile Indicator with Circle
    first_letter = st.session_state.username[0].upper() if st.session_state.username else "?"
    profile_html = f"""
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="background-color: #ff4b4b; color: white; border-radius: 4px; width: 40px; height: 40px; display: flex; justify-content: center; align-items: center; font-weight: bold; margin-right: 15px; font-size: 20px;">
            {first_letter}
        </div>
        <div style="font-size: 18px; font-weight: bold;">
            {st.session_state.username}
        </div>
    </div>
    """
    st.markdown(profile_html, unsafe_allow_html=True)
    
    if st.button("My Profile", use_container_width=True):
        st.session_state.page = "My Profile"
    


page = st.session_state.page

# --- PAGE: MY PROFILE ---
if page == "My Profile":
    st.title("My Profile")
    st.markdown(f"**Username:** {st.session_state.username}")
    
    # Calculate donated models
    models = db.load_models()
    my_models = [m for m in models if m.get("uploader") == st.session_state.username]
    
    if st.session_state.role == "viewer":
        st.metric("Models Donated", len(my_models))
    elif st.session_state.role == "admin":
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Models Donated", len(my_models))
        with col2:
            st.metric("Models Asked For Reference", 0)
    elif st.session_state.role == "super_admin":
        st.metric("Number of Models Added", len(models))

    
    st.markdown("---")
    st.subheader("Preferences")
    
    # Map index from session state
    theme_idx = 0 if st.session_state.theme == "Dark" else 1
    theme_choice = st.radio("App Theme", ["Dark", "Light"], index=theme_idx, horizontal=True)
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()
        
    st.markdown("---")
    if st.button("Logout", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "viewer"
        st.session_state.page = "Dashboard"
        st.session_state.ignore_cookie = True
        cookie_manager.delete("cm_username")
        cookie_manager.set("cm_username", "")
        st.rerun()

# --- PAGE: ADD A MODEL ---
elif page in ["Send a Model", "Add a Model"]:
    is_super = st.session_state.role == "super_admin"
    st.title("Add a New Model" if is_super else "Send a New Model")
    st.markdown("Fill out the details below to add a new model to the museum.")
    
    with st.form("add_model_form", clear_on_submit=True):
        title = st.text_input("Model Name", max_chars=100)
        desc = st.text_area("Description")
        img = st.file_uploader("Upload Image (Optional)", type=["jpg", "jpeg", "png", "webp"])
        
        submitted = st.form_submit_button("Add Model" if is_super else "Send Model")
        if submitted:
            if title:
                with st.spinner("Uploading..."):
                    status = "approved" if st.session_state.role == "super_admin" else "pending"
                    db.add_model(title, desc, img, uploader=st.session_state.username, status=status)
                if status == "approved":
                    st.success("Model added successfully! Switch to the Dashboard to see it.")
                else:
                    st.success("Model submitted for verification! A Super Admin will review it shortly.")
            else:
                st.error("Please provide at least a name for the model.")
    
# --- PAGE: DASHBOARD ---
elif page == "Dashboard":
    # Decorative Custom CSS for brutalist cards
    st.markdown("""
    <style>
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid var(--text-color) !important;
        border-radius: 0px !important;
        box-shadow: 5px 5px 0px #ff4b4b !important;
        transition: all 0.2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translate(-3px, -3px);
        box-shadow: 8px 8px 0px #ff4b4b !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="border-bottom: 4px solid #ff4b4b; margin-bottom: 30px; padding-bottom: 10px;">
        <h1 style="font-size: 2.5rem; margin: 0; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">Hi {st.session_state.username}</h1>
        <p style="font-size: 1.1rem; opacity: 0.7; text-transform: uppercase; font-weight: bold; margin-top: 5px;">Welcome to the Model Museum</p>
    </div>
    """, unsafe_allow_html=True)

    # --- MAIN CONTENT: GALLERY ---
    all_models = db.load_models()
    models = [m for m in all_models if m.get("status", "approved") == "approved"]

    if not models:
        st.info("The museum is currently empty. Go to the sidebar to add the first model!")
    else:
        cols_per_row = 3
        for i in range(0, len(models), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(models):
                    m = models[i + j]
                    with col:
                        with st.container(border=True):
                            st.subheader(m.get("title", "Untitled"))
                        
                            if m.get("image_url"):
                                st.image(m["image_url"], use_container_width=True)
                        
                            if m.get("description"):
                                st.write(m["description"])
                            
                            # Edit / Delete Section
                            if st.session_state.role in ["admin", "super_admin"]:
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
                                            if st.form_submit_button("Delete"):
                                                db.delete_model(m["id"])
                                                st.rerun()


# --- PAGE: APPROVE A MODEL ---
elif page == "Approve a Model" and st.session_state.role == "super_admin":
    st.title("Approve a Model")
    st.markdown("Review models submitted by viewers and admins.")
    
    all_models = db.load_models()
    pending_models = [m for m in all_models if m.get("status") == "pending"]
    if not pending_models:
        st.info("No models pending verification.")
    else:
        for m in pending_models:
            with st.container():
                st.write(f"**{m.get('title', 'Untitled')}** by {m.get('uploader', 'Unknown')}")
                if m.get("image_url"):
                    st.image(m["image_url"], width=200)
                if m.get("description"):
                    st.write(m["description"])
                col1, col2, _ = st.columns([1, 1, 4])
                with col1:
                    if st.button("Approve", key=f"app_{m['id']}"):
                        db.update_model_status(m['id'], "approved")
                        st.rerun()
                with col2:
                    if st.button("Reject", key=f"rej_{m['id']}"):
                        db.delete_model(m['id'])
                        st.rerun()
                st.markdown("---")

# --- PAGE: SUPER ADMIN ---

if page == "Super Admin":
    if st.session_state.username.lower() != "abhinavk":
        st.error("Access Denied.")
        st.stop()
        
    st.title("Super Admin Panel")
    st.markdown(f"Welcome to the master control panel, **{st.session_state.username}**.")
    
    
    st.subheader("User Management")
    users_dict = db.get_all_users()
    
    if not users_dict:
        st.info("No users have logged in yet.")
    else:
        for u_name, u_role in users_dict.items():
            if u_name.lower() == "abhinavk": continue # Cannot change super admin
            
            with st.container():
                ucol1, ucol2, ucol3, ucol4 = st.columns([2, 1, 1, 1])
                with ucol1:
                    st.write(f"**{u_name}** ({u_role.upper()})")
                
                with ucol2:
                    if u_role == "banned":
                        st.write("") # empty
                    elif u_role != "admin":
                        if st.button("Promote", key=f"promo_{u_name}"):
                            db.set_user_role(u_name, "admin")
                            st.rerun()
                
                with ucol3:
                    if u_role == "banned":
                        if st.button("Unban", key=f"unban_{u_name}"):
                            db.set_user_role(u_name, "viewer")
                            st.rerun()
                    elif u_role != "viewer":
                        if st.button("Demote", key=f"demo_{u_name}"):
                            db.set_user_role(u_name, "viewer")
                            st.rerun()
                
                with ucol4:
                    if u_role != "banned":
                        if st.button("Ban", type="primary", key=f"ban_{u_name}"):
                            db.set_user_role(u_name, "banned")
                            st.rerun()
                            
                st.markdown("---")

