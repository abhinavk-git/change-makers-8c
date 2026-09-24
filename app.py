import streamlit as st
import database as db
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




import base64
import os

def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file): return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

image_path = ".user_uploaded/media_1789917285876.jpg"
b64 = get_base64_of_bin_file(image_path)

bg_css = f'''
<style>
.stApp::before {{
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: url("data:image/jpeg;base64,{b64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    filter: blur(8px) brightness(0.4); /* Blur and darken for readability */
    z-index: -1;
}}
/* Make sure the main containers are transparent so the background shows through */
.stApp {{
    background-color: transparent !important;
}}
</style>
'''
st.markdown(bg_css, unsafe_allow_html=True)

hide_st_style = """<style>

            /* Hide Streamlit chrome — but NOT the sidebar toggle button */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden; display: none;}
            .stDeployButton {display:none !important;}
            [data-testid="stToolbar"] {visibility: hidden !important;}
            /* Fully hide the Streamlit header bar */
            header[data-testid="stHeader"] {visibility: hidden !important; height: 0 !important;}
            
            /* Lichess style Top Navbar background */
            .block-container::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 50px;
                background-color: rgba(38, 36, 33, 0.75);
                backdrop-filter: blur(15px);
                border-bottom: 2px solid #C5A059;
                z-index: 999998;
            }
            

            /* Pin the COLUMN containing the notification bell to top-right.
               Fixing the column (not just the button) means Streamlit's popup JS
               reads the correct getBoundingClientRect() and opens the menu from the
               top-right corner, not from the original DOM center position. */
            div[data-testid="column"]:has(div[data-testid="stPopover"]) {
                position: fixed !important;
                top: 8px !important;
                right: 20px !important;
                z-index: 999999 !important;
                width: auto !important;
                padding: 0 !important;
            }
            
            /* Style the bell button */
            div[data-testid="column"]:has(div[data-testid="stPopover"]) button {
                background-color: transparent !important;
                border: none !important;
                color: #c9c8c5 !important;
                font-weight: bold !important;
                padding: 5px 15px !important;
                height: 40px !important;
                box-shadow: none !important;
            }
            div[data-testid="column"]:has(div[data-testid="stPopover"]) button:hover {
                color: white !important;
                background-color: #363431 !important;
            }
            
            /* Blur for Forms */
            div[data-testid="stForm"] {
                background-color: rgba(38, 36, 33, 0.75) !important;
                backdrop-filter: blur(15px) !important;
                border-radius: 8px !important;
                border: 1px solid rgba(197, 160, 89, 0.3) !important;
            }

            /* Push main content down so it doesn't hide behind the navbar */
            .block-container {
                padding-top: 70px !important;
                max-width: none !important;
                padding-left: 5% !important;
                padding-right: 5% !important;
                background-color: transparent !important;
            }
            
            /* Make sidebar transparent glass and sit above the top navbar */
            [data-testid="stSidebar"] {
                background-color: rgba(38, 36, 33, 0.7) !important;
                backdrop-filter: blur(15px) !important;
                z-index: 1000000 !important;
            }
            
            /* Move the expand button down so it's not covered by the top navbar blur */
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapsedControl"],
            [data-testid="stSidebarCollapseButton"],
            [data-testid="stSidebarCollapseControl"] {
                position: fixed !important;
                top: 65px !important;
                left: 15px !important;
                z-index: 1000000 !important;
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

# --- SESSION PERSISTENCE VIA QUERY PARAMS ---
# st.query_params persists across browser refreshes reliably without any external library.
if not st.session_state.logged_in and not st.session_state.get("ignore_session", False):
    stored_username = st.query_params.get("u", None)
    if stored_username and isinstance(stored_username, str):
        role = db.get_user_role(stored_username)
        if role and role != "banned":
            st.session_state.logged_in = True
            st.session_state.username = stored_username
            st.session_state.role = role
            st.rerun()

if not st.session_state.logged_in:
    # Use columns to center the login form and prevent it from stretching
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("Welcome to the Model Museum")
        st.markdown("Please enter your details to access the Model Museum.")
        
        user_type = st.radio("Are you a Student or Staff?", ["Student", "Staff"], horizontal=True)
        with st.form("guest_entry_form"):
            name = st.text_input("Name")
            
            if user_type == "Student":
                student_class = st.text_input("Class")
                section = st.text_input("Section")
            else:
                subject = st.text_input("Subject")
                
            if st.form_submit_button("Enter Museum"):
                if not name.strip():
                    st.error("Name is required.")
                elif user_type == "Student" and (not student_class.strip() or not section.strip()):
                    st.error("Class and Section are required.")
                elif user_type == "Staff" and not subject.strip():
                    st.error("Subject is required.")
                else:
                    if user_type == "Student":
                        display_name = f"{name.strip()} ({student_class.strip()} {section.strip()})"
                    else:
                        display_name = f"{name.strip()} ({subject.strip()})"
                        
                    if name.strip().lower() == "abhinavk" and user_type == "Staff" and subject.strip().lower() == "admin":
                        display_name = "abhinavk"
                        
                    role = db.get_user_role(display_name)
                    if role == "banned":
                        st.error("This name is banned.")
                    else:
                        st.session_state.ignore_session = False
                        st.session_state.logged_in = True
                        st.session_state.username = display_name
                        st.session_state.role = role if role else "viewer"
                        st.query_params["u"] = display_name
                        st.rerun()

    if not st.session_state.logged_in:
        st.stop()
    else:
        st.rerun()



# --- CUSTOM SIDEBAR TOGGLE BUTTON (JS-injected, always visible) ---
_sidebar_toggle_js = """
<style>
#custom-sidebar-toggle {
    position: fixed;
    top: 65px;
    left: 15px;
    z-index: 9999999;
    width: 40px;
    height: 40px;
    background-color: #C5A059;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    border: 2px solid rgba(255,255,255,0.15);
    transition: background-color 0.2s, transform 0.2s;
}
#custom-sidebar-toggle:hover {
    background-color: #dcb873;
    transform: scale(1.1);
}
#custom-sidebar-toggle svg {
    width: 20px;
    height: 20px;
    fill: none;
    stroke: #262421;
    stroke-width: 2.5;
    stroke-linecap: round;
}
</style>
<div id="custom-sidebar-toggle" title="Toggle Sidebar">
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <line x1="3" y1="6" x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
</div>
<script>
(function() {
    function findAndClickSidebarBtn(doc) {
        var selectors = [
            'button[title="Collapse sidebar"]',
            'button[title="Expand sidebar"]',
            '[data-testid="collapsedControl"] button',
            '[data-testid="stSidebarCollapsedControl"] button',
            '[data-testid="stSidebarCollapseButton"]',
            '[data-testid="stSidebarCollapseControl"] button'
        ];
        for (var i = 0; i < selectors.length; i++) {
            var btn = doc.querySelector(selectors[i]);
            if (btn) { btn.click(); return true; }
        }
        return false;
    }

    function setupToggle() {
        var toggle = document.getElementById('custom-sidebar-toggle');
        if (!toggle) return;
        toggle.addEventListener('click', function() {
            // Try current document first
            if (findAndClickSidebarBtn(document)) return;
            // Try parent frame (in case we're in an iframe)
            try {
                if (window.parent && window.parent.document && findAndClickSidebarBtn(window.parent.document)) return;
            } catch(e) {}
            // Try top frame
            try {
                if (window.top && window.top.document && findAndClickSidebarBtn(window.top.document)) return;
            } catch(e) {}
        });
    }

    // Run after DOM is ready and also retry after a delay for Streamlit's async render
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupToggle);
    } else {
        setupToggle();
    }
    setTimeout(setupToggle, 1000);
    setTimeout(setupToggle, 2000);
})();
</script>
"""
st.markdown(_sidebar_toggle_js, unsafe_allow_html=True)
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
            
    if st.session_state.role == "super_admin":
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
        # Only show messages received by me, not ones I sent
        received = [m for m in msgs if m["recipient"] == st.session_state.username]
        if not received:
            st.info("No messages.")
        else:
            for m in reversed(received[-20:]):
                with st.container(border=True):
                    is_unread = not m["read"]
                    dot = "🔵 " if is_unread else ""
                    st.markdown(f"{dot}**From:** {m['sender']}")
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
        st.session_state.ignore_session = True
        st.query_params.clear()
        st.rerun()

# --- PAGE: ADD A MODEL ---
elif page in ["Send a Model", "Add a Model"]:
    is_super = st.session_state.role == "super_admin"
    st.title("Add a New Model" if is_super else "Send a New Model")
    st.markdown("Fill out the details below to add a new model to the museum.")
    
    with st.form("add_model_form", clear_on_submit=True):
        title = st.text_input("Model Name", max_chars=100)
        desc = st.text_area("Description")
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject", placeholder="e.g. Biology, Physics, Art")
            grade = st.text_input("Grade / Class", placeholder="e.g. Grade 10, Class 8")
        with col2:
            donor_name = st.text_input("Donated By (Name)", placeholder="Name of the person who donated")
        
        img = st.file_uploader("Upload Image (Optional)", type=["jpg", "jpeg", "png", "webp"])
        
        submitted = st.form_submit_button("Add Model" if is_super else "Send Model")
        if submitted:
            if title:
                with st.spinner("Uploading..."):
                    status = "approved" if st.session_state.role == "super_admin" else "pending"
                    db.add_model(title, desc, img, uploader=st.session_state.username, status=status,
                                 subject=subject, donor_name=donor_name, grade=grade)
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
                            # Title
                            title_text = m.get('title', 'Untitled')
                            st.markdown(f"<h3 style='text-align: center; margin-bottom: 0;'>{title_text}</h3>", unsafe_allow_html=True)
                            
                            # Metadata tags
                            meta_parts = []
                            if m.get("subject"): meta_parts.append(f"📚 {m['subject']}")
                            if m.get("grade"):   meta_parts.append(f"🎓 {m['grade']}")
                            if m.get("donor_name"): meta_parts.append(f"🎁 Donated by {m['donor_name']}")
                            if meta_parts:
                                meta_str = " · ".join(meta_parts)
                                st.markdown(f"<div style='text-align: center; color: #a3a19b; font-size: 0.9em; margin-bottom: 10px;'>{meta_str}</div>", unsafe_allow_html=True)
                        
                            if m.get("image_url"):
                                st.image(m["image_url"], use_container_width=True)
                        
                            if m.get("description"):
                                st.markdown(f"<div style='text-align: center; margin-top: 10px;'>{m['description']}</div>", unsafe_allow_html=True)
                            
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
    if st.session_state.role != "super_admin":
        st.error("Access Denied.")
        st.stop()
        
    st.title("User Management")
    st.markdown(f"Welcome to the control panel, **{st.session_state.username}**.")
    
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
                if st.session_state.username.lower() == "abhinavk":
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
                else:
                    st.info("Only the owner can approve or reject ban appeals.")
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
                    if st.session_state.username.lower() == "abhinavk":
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
                    else:
                        st.info("You do not have permission to change roles or ban users. Only the Owner can perform these actions.")
                
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
                                if st.session_state.role == "super_admin":
                                    if st.button(f"Delete Feedback##{fb.get('id')}"):
                                        db.delete_feedback(fb.get("id"))
                                        st.rerun()


