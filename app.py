import streamlit as st
import database as db

st.set_page_config(page_title="Change Makers 8c", page_icon="🏛️", layout="wide")

# --- FIREBASE AUTHENTICATION SETUP ---
auth = None
USE_FIREBASE_AUTH = False

try:
    if "firebase_api_key" in st.secrets and "firebase_project_id" in st.secrets:
        import pyrebase
        config = {
            "apiKey": st.secrets["firebase_api_key"],
            "authDomain": f"{st.secrets['firebase_project_id']}.firebaseapp.com",
            "projectId": st.secrets["firebase_project_id"],
            "databaseURL": "",
            "storageBucket": f"{st.secrets['firebase_project_id']}.appspot.com",
            "messagingSenderId": "",
            "appId": "",
            "measurementId": ""
        }
        firebase_app = pyrebase.initialize_app(config)
        auth = firebase_app.auth()
        USE_FIREBASE_AUTH = True
except Exception as e:
    print("Firebase Auth setup failed:", e)


# --- LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🔒 Login Required")
    st.markdown("Please log in or create an account to access the Model Museum.")
    
    if USE_FIREBASE_AUTH:
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    # Hack: Firebase requires an email, so we fake one using the username!
                    fake_email = f"{username.lower().replace(' ', '')}@changemakers.local"
                    try:
                        user = auth.sign_in_with_email_and_password(fake_email, password)
                        st.session_state.logged_in = True
                        st.session_state.username = username
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
        st.warning("Firebase Authentication is not configured yet. Falling back to simple admin password.")
        with st.form("simple_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                correct_username = st.secrets.get("admin_username", "admin")
                correct_password = st.secrets.get("admin_password", "changemakers")
                if username == correct_username and password == correct_password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
                    
    st.stop() # Stop rendering the rest of the app until logged in

# --- LOGOUT BUTTON ---
with st.sidebar:
    st.markdown(f"**Logged in as:** {st.session_state.username}")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
    st.divider()

# --- MAIN APP BELOW ---
st.title("🏛️ Change Makers Model Museum")
st.markdown("Welcome to the Model Museum! Explore our models or add your own.")

# --- SIDEBAR: ADD NEW MODEL ---
with st.sidebar:
    st.header("Add New Model")
    with st.form("add_model_form", clear_on_submit=True):
        title = st.text_input("Model Name", max_chars=100)
        desc = st.text_area("Description")
        img = st.file_uploader("Upload Image (Drag & Drop here)", type=["jpg", "jpeg", "png", "webp"])
        
        submitted = st.form_submit_button("Add Model")
        if submitted:
            if title and img:
                with st.spinner("Optimizing and uploading..."):
                    db.add_model(title, desc, img)
                st.success("Model added successfully!")
                st.rerun()
            else:
                st.error("Please provide a name and an image.")

# --- MAIN CONTENT: GALLERY ---
models = db.load_models()

if not models:
    st.info("The museum is currently empty. Be the first to add a model using the sidebar!")
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
