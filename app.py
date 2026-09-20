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
    
            """, unsafe_allow_html=True)




hide_st_style = """<style>
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
                border-radius: 3px !important;
            }
            
            /* Lichess style Top Navbar background */
            .block-container::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 50px;
                background-color: #262421;
                border-bottom: 2px solid #C5A059;
                z-index: 999998;
            }
            

            /* Pin the popover button to the right side of the Navbar */
            div[data-testid="stPopover"] {
                transform: none !important;
                position: fixed !important;
                top: 5px !important;
                right: 20px !important;
                z-index: 999999 !important;
            }
            
            /* Style the button itself to look like Lichess */
            div[data-testid="stPopover"] button {
                background-color: transparent !important;
                border: none !important;
                color: #c9c8c5 !important;
                font-weight: bold;
                padding: 5px 15px !important;
                height: 40px !important;
                box-shadow: none !important;
            }
            
            div[data-testid="stPopover"] button:hover {
                color: white !important;
                background-color: #363431 !important;
                transform: none !important;
            }
            
            
            /* Blur for Popover menus and Forms */
            div[data-testid="stPopoverBody"], div[data-testid="stForm"] {
                background-color: rgba(38, 36, 33, 0.75) !important;
                backdrop-filter: blur(15px) !important;
                border-radius: 8px !important;
                border: 1px solid rgba(197, 160, 89, 0.3) !important;
            }
            
            
            /* Force the popover menu to appear on the right side under the button */
            div[data-testid="stPopoverBody"] {
                transform: none !important;
                right: 20px !important;
                left: auto !important;
                top: 55px !important;
                position: fixed !important;
            }

            /* Push main content down so it doesn't hide behind the navbar */
            .block-container {
                padding-top: 70px !important;
                max-width: none !important;
                padding-left: 5% !important;
                padding-right: 5% !important;
            }
            
            """



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

# --- COOKIE MANAGER (12 HR PERSISTENT LOGIN) ---
cookie_manager = stx.CookieManager(key="cookie_manager")

# Wait for cookies to load from frontend.
# We stop exactly ONCE (on the very first execution tick) so the cookie manager
# can complete one round-trip with the browser. On tick 1+ we always continue,
# regardless of whether cookies is None or {}.
if "cookie_load_tick" not in st.session_state:
    st.session_state.cookie_load_tick = 0

cookies = cookie_manager.get_all()
if st.session_state.cookie_load_tick == 0:
    st.session_state.cookie_load_tick = 1
    st.stop()




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
                            role = db.get_user_role(username)
                            if role == "banned":
                                active_ban = db.get_active_ban(username)
                                reason = active_ban.get("reason", "No reason provided.") if active_ban else "Violations of policy."
                                st.error(f"**ACCOUNT BANNED**\n\n**Reason:** {reason}")
                                
                                if active_ban and active_ban.get("appeal_status") == "pending":
                                    st.info("Your appeal is currently under review by the Owner.")
                                else:
                                    with st.expander("Appeal Ban"):
                                        with st.form("appeal_form"):
                                            appeal_text = st.text_area("Why should your ban be lifted?")
                                            if st.form_submit_button("Submit Appeal"):
                                                if appeal_text.strip():
                                                    db.submit_ban_appeal(username, appeal_text.strip())
                                                    st.success("Appeal submitted successfully.")
                                                else:
                                                    st.error("Please enter an appeal message.")
                            else:
                                st.session_state.ignore_cookie = False
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.role = role
                                # Set cookie for 12 hours
                                cookie_manager.set("cm_username", username, expires_at=datetime.datetime.now() + datetime.timedelta(hours=12))
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
                            active_ban = db.get_active_ban(username.strip())
                            reason = active_ban.get("reason", "No reason provided.") if active_ban else "Violations of policy."
                            st.error(f"**ACCOUNT BANNED**\n\n**Reason:** {reason}")
                            
                            if active_ban and active_ban.get("appeal_status") == "pending":
                                st.info("Your appeal is currently under review by the Owner.")
                            else:
                                with st.expander("Appeal Ban"):
                                    with st.form("appeal_form2"):
                                        appeal_text = st.text_area("Why should your ban be lifted?")
                                        if st.form_submit_button("Submit Appeal"):
                                            if appeal_text.strip():
                                                db.submit_ban_appeal(username.strip(), appeal_text.strip())
                                                st.success("Appeal submitted successfully.")
                                            else:
                                                st.error("Please enter an appeal message.")
                        else:
                            st.session_state.ignore_cookie = False
                            st.session_state.logged_in = True
                            st.session_state.username = username.strip()
                            st.session_state.role = role
                            cookie_manager.set("cm_username", username.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(hours=12))
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
    st.markdown(hide_st_style, unsafe_allow_html=True)
    st.title("Museum Menu")
    if st.button("Dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"
    action_name = "Add a Model" if st.session_state.role == "super_admin" else "Send a Model"
    if st.button(action_name, use_container_width=True):
        st.session_state.page = action_name
        
    if st.button("About Us", use_container_width=True):
        st.session_state.page = "About Us"
        
    if st.button("Feedback", use_container_width=True):
        st.session_state.page = "Feedback"
        
    if st.session_state.role == "super_admin":
        if st.button("Approve a Model", use_container_width=True):
            st.session_state.page = "Approve a Model"
            
    if st.session_state.username.lower() == "abhinavk":
        if st.button("User Management", use_container_width=True):
            st.session_state.page = "Super Admin"
            
    st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)
    
    # Profile Indicator with Circle
    first_letter = st.session_state.username[0].upper() if st.session_state.username else "?"
    profile_html = f"""
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="background-color: #C5A059; color: white; border-radius: 4px; width: 40px; height: 40px; display: flex; justify-content: center; align-items: center; font-weight: bold; margin-right: 15px; font-size: 20px;">
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

# --- GLOBAL NOTIFICATION BELL ---
unread_count = db.get_unread_count(st.session_state.username)
bell_icon = f"🔔 Notifications ({unread_count})" if unread_count > 0 else "🔔 Notifications"

# Place the bell in the rightmost column so Streamlit's JS anchors the popup on the right
_bell_spacer, _bell_col = st.columns([10, 1])
with _bell_col:
    with st.popover(bell_icon, use_container_width=True):
        st.subheader("Direct Messages")
        
        # Message sending
        all_users = db.get_all_users()
        other_users = [u for u in all_users.keys() if u != st.session_state.username]
        with st.form("send_msg_form", clear_on_submit=True):
            recipient = st.selectbox("To:", other_users)
            msg_text = st.text_area("Message:")
            if st.form_submit_button("Send"):
                if recipient and msg_text.strip():
                    db.send_message(st.session_state.username, recipient, msg_text.strip())
                    st.success("Sent!")
        
        st.markdown("---")
        if unread_count > 0:
            if st.button("Mark all as read", type="primary", use_container_width=True):
                db.mark_messages_read(st.session_state.username)
                st.rerun()
                
        # Message list
        msgs = db.get_messages_for_user(st.session_state.username)
        if not msgs:
            st.info("No messages.")
        else:
            for m in reversed(msgs[-20:]): # Only show last 20 messages
                with st.container(border=True):
                    is_unread = not m["read"] and m["recipient"] == st.session_state.username
                    dot = "🔵 " if is_unread else ""
                    st.markdown(f"{dot}**From:** {m['sender']} | **To:** {m['recipient']}")
                    st.caption(m['timestamp'])
                    st.write(m['text'])


    
    
# --- PAGE: ABOUT US ---
if page == "About Us":
    st.markdown("""
    <div style="border-bottom: 2px solid #C5A059; margin-bottom: 30px; padding-bottom: 10px;">
        <h1 style="font-size: 2.5rem; margin: 0; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">About Us</h1>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    Welcome to the **Model Museum**! 
    
    This platform is dedicated to showcasing incredible models and creations from our community. 
    Our mission is to provide a curated, easily accessible space for everyone to share their work, 
    learn from others, and get inspired.
    """)

# --- PAGE: FEEDBACK ---
elif page == "Feedback":
    st.markdown("""
    <div style="border-bottom: 2px solid #C5A059; margin-bottom: 30px; padding-bottom: 10px;">
        <h1 style="font-size: 2.5rem; margin: 0; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">Feedback</h1>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("We'd love to hear your thoughts! Let us know how we can improve the museum.")
    
    with st.form("feedback_form", clear_on_submit=True):
        feedback_text = st.text_area("Your Feedback")
        if st.form_submit_button("Submit"):
            if feedback_text.strip():
                import datetime
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                
                # Check how many feedback they submitted today
                all_fb = db.get_all_feedback()
                todays_fb_count = sum(1 for fb in all_fb if fb.get("username") == st.session_state.username and fb.get("date", "").startswith(today_str))
                
                if todays_fb_count >= 5:
                    st.error("You have reached the limit of 5 feedback submissions per day. Please come back tomorrow!")
                else:
                    db.save_feedback(st.session_state.username, feedback_text.strip())
                    st.success("Thank you for your feedback! It has been sent directly to the owner.")
            else:
                st.error("Please enter some feedback before submitting.")

# --- PAGE: MY PROFILE ---
elif page == "My Profile":
    st.title("My Profile")
    st.markdown(f"**Username:** {st.session_state.username}")
    
    # Format the position
    if st.session_state.username.lower() == "abhinavk":
        display_role = "Owner (Super Admin)"
    else:
        display_role = st.session_state.role.replace("_", " ").title()
        
    st.markdown(f"""
    <div style="margin-top: 15px; margin-bottom: 25px;">
        <span style="font-size: 1.1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Current Position</span><br>
        <div style="display: inline-block; background-color: transparent; color: #C5A059; padding: 8px 18px; font-weight: 900; font-size: 1.4rem; letter-spacing: 2px; text-transform: uppercase; margin-top: 8px; border: 1px solid #C5A059; box-shadow: 0px 4px 15px rgba(197, 160, 89, 0.2); border-radius: 3px;">
            {display_role}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    if USE_FIREBASE_AUTH:
        if auth:
            st.markdown("<br><h3 style='color: #C5A059;'>Change Password</h3>", unsafe_allow_html=True)
            with st.form("change_password_form", clear_on_submit=True):
                current_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                
                if st.form_submit_button("Update Password"):
                    if not current_pw or not new_pw:
                        st.error("Please fill in both fields.")
                    elif len(new_pw) < 6:
                        st.error("New password must be at least 6 characters.")
                    else:
                        fake_email = f"{st.session_state.username.lower().replace(' ', '')}@changemakers.local"
                        try:
                            # Re-authenticate to get a fresh token
                            user = auth.sign_in_with_email_and_password(fake_email, current_pw)
                            # Change the password using the token
                            auth.change_password(user['idToken'], new_pw)
                            st.success("Password successfully updated!")
                        except Exception as e:
                            try:
                                import json
                                error_data = json.loads(e.args[1])
                                err_msg = error_data['error']['message']
                                if err_msg == "INVALID_LOGIN_CREDENTIALS" or err_msg == "INVALID_PASSWORD":
                                    st.error("Incorrect current password.")
                                else:
                                    st.error(f"Error: {err_msg}")
                            except:
                                st.error("Incorrect current password or an error occurred.")

    
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
        border: 1px solid rgba(197, 160, 89, 0.3) !important;
        border-radius: 4px !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.5) !important;
        background: rgba(38, 36, 33, 0.75) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
        box-shadow: 0px 8px 25px rgba(197, 160, 89, 0.15) !important;
        border: 1px solid #C5A059 !important;
    }
    
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="border-bottom: 2px solid #C5A059; margin-bottom: 30px; padding-bottom: 10px;">
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
        
    st.title("User Management")
    st.markdown(f"Welcome to the owner control panel, **{st.session_state.username}**.")
    
    users_dict = db.get_all_users()
    
    # 1. Show Appeal Notifications
    pending_appeals = db.get_pending_appeals()
    if pending_appeals:
        st.error("🚨 **ACTION REQUIRED: PENDING BAN APPEALS** 🚨")
        for app in pending_appeals:
            with st.container(border=True):
                st.write(f"**User:** {app['username']}")
                st.write(f"**Original Ban Reason:** {app['reason']}")
                st.write(f"**Appeal Message:** {app['appeal']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Approve Appeal (Unban)##{app['username']}", type="primary"):
                        db.resolve_ban_appeal(app['username'], unban=True)
                        st.toast(f"{app['username']} has been unbanned.")
                        st.rerun()
                with col2:
                    if st.button(f"Reject Appeal##{app['username']}"):
                        db.resolve_ban_appeal(app['username'], unban=False)
                        st.toast(f"Appeal from {app['username']} rejected.")
                        st.rerun()
        st.markdown("---")
    
    # 2. User Selection
    if not users_dict:
        st.info("No users have logged in yet.")
    else:
        user_list = [u for u in users_dict.keys() if u.lower() != "abhinavk"]
        if not user_list:
            st.info("No other users exist yet.")
        else:
            selected_user = st.selectbox("Select a User to moderate:", ["-- Select User --"] + user_list)
            
            if selected_user != "-- Select User --":
                u_role = users_dict[selected_user]
                st.markdown(f"### Profile: **{selected_user}** ({u_role.upper()})")
                
                tab1, tab2, tab3 = st.tabs(["Role Management", "Ban History", "Feedback Submitted"])
                
                with tab1:
                    st.subheader("Manage Role")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if u_role == "viewer":
                            if st.button("Promote to Admin", use_container_width=True):
                                db.set_user_role(selected_user, "admin")
                                st.rerun()
                        elif u_role == "admin":
                            if st.button("Promote to Super Admin", use_container_width=True):
                                db.set_user_role(selected_user, "super_admin")
                                st.rerun()
                        elif u_role == "super_admin":
                            if st.button("Demote to Admin", use_container_width=True):
                                db.set_user_role(selected_user, "admin")
                                st.rerun()
                    with col2:
                        if u_role == "admin":
                            if st.button("Demote to Viewer", use_container_width=True):
                                db.set_user_role(selected_user, "viewer")
                                st.rerun()
                    
                    st.markdown("---")
                    st.subheader("Ban User")
                    if u_role == "banned":
                        if st.button("Unban User", type="primary"):
                            db.resolve_ban_appeal(selected_user, unban=True)
                            st.rerun()
                    else:
                        with st.form("ban_form"):
                            ban_reason = st.text_area("Reason for banning:")
                            if st.form_submit_button("Ban User", type="primary"):
                                if ban_reason.strip():
                                    db.ban_user_with_reason(selected_user, ban_reason.strip())
                                    st.success(f"{selected_user} has been banned.")
                                    st.rerun()
                                else:
                                    st.error("You must provide a reason for the ban.")
                
                with tab2:
                    st.subheader("Ban History")
                    bans = db.get_user_bans(selected_user)
                    if not bans:
                        st.info("No ban history for this user.")
                    else:
                        for b in reversed(bans):
                            with st.container(border=True):
                                st.write(f"**Date:** {b['date']}")
                                st.write(f"**Reason:** {b['reason']}")
                                st.write(f"**Status:** {'Active' if b['active'] else 'Resolved'}")
                                if b.get('appeal'):
                                    st.write(f"**Appeal Message:** {b['appeal']} ({b.get('appeal_status', 'N/A')})")
                
                with tab3:
                    st.subheader("Feedback Submitted")
                    all_fb = db.get_all_feedback()
                    user_fb = [f for f in all_fb if f.get("username") == selected_user]
                    if not user_fb:
                        st.info("This user has not submitted any feedback.")
                    else:
                        for fb in reversed(user_fb):
                            with st.container(border=True):
                                st.write(f"**Date:** {fb.get('date', 'Unknown')}")
                                st.write(fb.get('text', ''))
                                if st.button(f"Delete Feedback##{fb.get('id')}"):
                                    db.delete_feedback(fb.get("id"))
                                    st.rerun()


if page == "Super Admin":
    if st.session_state.username.lower() != "abhinavk":
        st.error("Access Denied.")
        st.stop()
        
    st.title("User Management")
    st.markdown(f"Welcome to the owner control panel, **{st.session_state.username}**.")
    users_dict = db.get_all_users()
    
    # Show Feedback
    st.markdown("---")
    st.subheader("User Feedback")
    all_feedback = db.get_all_feedback()
    if not all_feedback:
        st.info("No feedback has been submitted yet.")
    else:
        for fb in reversed(all_feedback):
            with st.container(border=True):
                st.markdown(f"**From:** {fb['username']} | **Date:** {fb['date']}")
                st.write(fb['text'])

    st.markdown("---")
    st.subheader("User Roles")
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
                    if u_role == "viewer":
                        if st.button("Promote (Admin)", key=f"promo_{u_name}"):
                            db.set_user_role(u_name, "admin")
                            st.rerun()
                    elif u_role == "admin":
                        if st.button("Promote (Super)", key=f"promo_sa_{u_name}"):
                            db.set_user_role(u_name, "super_admin")
                            st.rerun()
                    else:
                        st.write("")
                
                with ucol3:
                    if u_role == "banned":
                        if st.button("Unban", key=f"unban_{u_name}"):
                            db.set_user_role(u_name, "viewer")
                            st.rerun()
                    elif u_role == "super_admin":
                        if st.button("Demote (Admin)", key=f"demo_a_{u_name}"):
                            db.set_user_role(u_name, "admin")
                            st.rerun()
                    elif u_role == "admin":
                        if st.button("Demote (Viewer)", key=f"demo_v_{u_name}"):
                            db.set_user_role(u_name, "viewer")
                            st.rerun()
                    else:
                        st.write("")
                
                with ucol4:
                    if u_role != "banned":
                        if st.button("Ban", type="primary", key=f"ban_{u_name}"):
                            db.set_user_role(u_name, "banned")
                            st.rerun()
                            
                st.markdown("---")

