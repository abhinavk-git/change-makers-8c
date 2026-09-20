import json
import os
import uuid
import datetime
import io
import base64
from PIL import Image
import streamlit as st

IMG_DIR = "images"
DB_FILE = "models.json"
os.makedirs(IMG_DIR, exist_ok=True)

# Firebase initialization
USE_FIREBASE = False
db = None

try:
    if "firebase_api_key" in st.secrets and "firebase_project_id" in st.secrets:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cert_dict = dict(st.secrets["firebase"])
            cert_dict["private_key"] = cert_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(cert_dict)
            project_id = cert_dict.get("project_id", "")
            
            # We removed the storageBucket requirement since Firebase Storage is not free for the user!
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()
        USE_FIREBASE = True
except Exception as e:
    print(f"Firebase setup skipped or failed: {e}")

# === LOCAL FALLBACK FUNCTIONS ===
def _load_local():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def _save_local(models):
    with open(DB_FILE, "w") as f: json.dump(models, f, indent=4)

# === IMAGE COMPRESSION ===
def process_image_to_base64(uploaded_file):
    if not uploaded_file: return None
    
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]: ext = "jpeg"
    
    try:
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")
        
        # Aggressive resize to ensure it fits in Firestore's 1MB document limit
        max_width = 800
        if image.width > max_width:
            ratio = max_width / image.width
            image = image.resize((max_width, int(image.height * ratio)), Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        # High compression
        image.save(img_byte_arr, format="JPEG", optimize=True, quality=60)
        
        img_bytes = img_byte_arr.getvalue()
        
        # If still too large, compress even more
        if len(img_bytes) > 700000:
            img_byte_arr = io.BytesIO()
            image = image.resize((600, int(image.height * (600/image.width))), Image.Resampling.LANCZOS)
            image.save(img_byte_arr, format="JPEG", optimize=True, quality=40)
            img_bytes = img_byte_arr.getvalue()
            
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"Error compressing image: {e}")
        return None

def _save_local_image(uploaded_file):
    b64_string = process_image_to_base64(uploaded_file)
    return b64_string # Just return the base64 string directly

# === PUBLIC DB API ===
def load_models():
    if USE_FIREBASE:
        models_ref = db.collection('models').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        return [doc.to_dict() for doc in models_ref]
    else:
        return _load_local()

def add_model(title, description, uploaded_file, uploader=""):
    model_id = uuid.uuid4().hex
    
    if USE_FIREBASE:
        image_b64 = process_image_to_base64(uploaded_file)
            
        doc_ref = db.collection('models').document(model_id)
        doc_ref.set({
            "id": model_id,
            "title": title,
            "description": description,
            "image_url": image_b64,
            "uploader": uploader,
            "created_at": firestore.SERVER_TIMESTAMP
        })
    else:
        models = _load_local()
        image_b64 = process_image_to_base64(uploaded_file)
        models.append({
            "id": model_id,
            "title": title,
            "description": description,
            "image_url": image_b64,
            "uploader": uploader,
            "created_at": str(datetime.datetime.now())
        })
        _save_local(models)

def update_model(model_id, title, description, uploaded_file=None):
    if USE_FIREBASE:
        doc_ref = db.collection('models').document(model_id)
        doc = doc_ref.get()
        if not doc.exists: return
        
        data = {"title": title, "description": description}
        
        if uploaded_file:
            data["image_url"] = process_image_to_base64(uploaded_file)
                
        doc_ref.update(data)
    else:
        models = _load_local()
        for m in models:
            if m["id"] == model_id:
                m["title"] = title
                m["description"] = description
                if uploaded_file:
                    m["image_url"] = process_image_to_base64(uploaded_file)
                break
        _save_local(models)

def delete_model(model_id):
    if USE_FIREBASE:
        db.collection('models').document(model_id).delete()
    else:
        models = _load_local()
        models = [m for m in models if m["id"] != model_id]
        _save_local(models)

# === USER MANAGEMENT ===
USERS_FILE = "users.json"
def _load_users_local():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, "r") as f: return json.load(f)
    except: return {}

def _save_users_local(users_dict):
    with open(USERS_FILE, "w") as f: json.dump(users_dict, f, indent=4)

def get_user_role(username):
    if not isinstance(username, str):
        try:
            username = str(username)
        except:
            return "viewer"
    username = username.lower().strip()
    if username == "abhinavk":
        return "super_admin"
        
    if USE_FIREBASE:
        doc_ref = db.collection('users').document(username)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("role", "viewer")
        else:
            doc_ref.set({"role": "viewer"})
            return "viewer"
    else:
        users = _load_users_local()
        if username in users:
            return users[username]
        else:
            users[username] = "viewer"
            _save_users_local(users)
            return "viewer"

def set_user_role(username, role):
    username = username.lower().strip()
    if username == "abhinavk": return # Cannot change super admin
    
    if USE_FIREBASE:
        db.collection('users').document(username).set({"role": role})
    else:
        users = _load_users_local()
        users[username] = role
        _save_users_local(users)

def get_all_users():
    if USE_FIREBASE:
        users_ref = db.collection('users').stream()
        # Return dict of username: role
        return {doc.id: doc.to_dict().get("role", "viewer") for doc in users_ref}
    else:
        return _load_users_local()

# --- FEEDBACK ---
FEEDBACK_FILE = "feedback.json"

def get_all_feedback():
    if not os.path.exists(FEEDBACK_FILE): return []
    try:
        with open(FEEDBACK_FILE, "r") as f: return json.load(f)
    except: return []

def save_feedback(username, text):
    feedback = get_all_feedback()
    import datetime
    entry = {
        "id": str(int(datetime.datetime.now().timestamp() * 1000)),
        "username": username,
        "text": text,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    feedback.append(entry)
    with open(FEEDBACK_FILE, "w") as f: json.dump(feedback, f, indent=4)

def delete_feedback(feedback_id):
    feedback = get_all_feedback()
    feedback = [f for f in feedback if f.get("id") != feedback_id]
    with open(FEEDBACK_FILE, "w") as f: json.dump(feedback, f, indent=4)

# --- BANS & APPEALS ---
BANS_FILE = "bans.json"

def _load_bans():
    if not os.path.exists(BANS_FILE): return {}
    try:
        with open(BANS_FILE, "r") as f: return json.load(f)
    except: return {}

def _save_bans(bans_dict):
    with open(BANS_FILE, "w") as f: json.dump(bans_dict, f, indent=4)

def get_user_bans(username):
    bans = _load_bans()
    return bans.get(username, [])

def get_active_ban(username):
    bans = get_user_bans(username)
    for b in bans:
        if b.get("active", False):
            return b
    return None

def ban_user_with_reason(username, reason):
    import datetime
    bans = _load_bans()
    if username not in bans:
        bans[username] = []
    
    # Mark any existing active bans as inactive
    for b in bans[username]:
        b["active"] = False
        
    bans[username].append({
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "reason": reason,
        "active": True,
        "appeal": None,
        "appeal_status": None
    })
    _save_bans(bans)
    set_user_role(username, "banned")

def submit_ban_appeal(username, appeal_text):
    bans = _load_bans()
    if username in bans:
        for b in bans[username]:
            if b.get("active", False):
                b["appeal"] = appeal_text
                b["appeal_status"] = "pending"
                break
    _save_bans(bans)

def resolve_ban_appeal(username, unban=True):
    bans = _load_bans()
    if username in bans:
        for b in bans[username]:
            if b.get("active", False):
                b["active"] = not unban
                b["appeal_status"] = "approved" if unban else "rejected"
                break
    _save_bans(bans)
    if unban:
        set_user_role(username, "viewer")

def get_pending_appeals():
    bans = _load_bans()
    appeals = []
    for uname, user_bans in bans.items():
        for b in user_bans:
            if b.get("active", False) and b.get("appeal_status") == "pending":
                appeals.append({"username": uname, "appeal": b.get("appeal"), "reason": b.get("reason")})
    return appeals
