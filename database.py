import json
import os
import uuid
import datetime
import io
from PIL import Image
import streamlit as st

IMG_DIR = "images"
DB_FILE = "models.json"
os.makedirs(IMG_DIR, exist_ok=True)

# Firebase initialization
USE_FIREBASE = False
db = None
bucket = None

try:
    if "firebase" in st.secrets:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage

        if not firebase_admin._apps:
            cert_dict = dict(st.secrets["firebase"])
            # Ensure private key has proper line breaks
            cert_dict["private_key"] = cert_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(cert_dict)
            project_id = cert_dict.get("project_id", "")
            bucket_name = f"{project_id}.firebasestorage.app"
            
            # Using firebasestorage.app is the modern domain, or appspot.com
            # Let's use appspot.com which is the standard default
            firebase_admin.initialize_app(cred, {
                'storageBucket': f"{project_id}.appspot.com"
            })
            
        db = firestore.client()
        bucket = storage.bucket()
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
def process_image(uploaded_file):
    if not uploaded_file: return None, None, None
    
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]: ext = "jpeg"
    
    try:
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")
        
        max_width = 1200
        if image.width > max_width:
            ratio = max_width / image.width
            image = image.resize((max_width, int(image.height * ratio)), Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        if ext in ["jpg", "jpeg"]:
            image.save(img_byte_arr, format="JPEG", optimize=True, quality=80)
            content_type = "image/jpeg"
        elif ext == "webp":
            image.save(img_byte_arr, format="WEBP", optimize=True, quality=80)
            content_type = "image/webp"
        else:
            image.save(img_byte_arr, format="PNG", optimize=True)
            content_type = "image/png"
            
        return img_byte_arr.getvalue(), ext, content_type
    except Exception as e:
        print(f"Error compressing image: {e}")
        return None, None, None

def _save_local_image(uploaded_file):
    img_bytes, ext, _ = process_image(uploaded_file)
    if not img_bytes: return None
    
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(IMG_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(img_bytes)
    return filepath

# === PUBLIC DB API ===
def load_models():
    if USE_FIREBASE:
        models_ref = db.collection('models').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        return [doc.to_dict() for doc in models_ref]
    else:
        return _load_local()

def add_model(title, description, uploaded_file):
    model_id = uuid.uuid4().hex
    image_url = None
    
    if USE_FIREBASE:
        img_bytes, ext, content_type = process_image(uploaded_file)
        if img_bytes:
            filename = f"models/{model_id}.{ext}"
            blob = bucket.blob(filename)
            blob.upload_from_string(img_bytes, content_type=content_type)
            blob.make_public()
            image_url = blob.public_url
            
        doc_ref = db.collection('models').document(model_id)
        doc_ref.set({
            "id": model_id,
            "title": title,
            "description": description,
            "image_url": image_url,
            "created_at": firestore.SERVER_TIMESTAMP
        })
    else:
        # Fallback to local
        models = _load_local()
        image_url = _save_local_image(uploaded_file)
        models.append({
            "id": model_id,
            "title": title,
            "description": description,
            "image_url": image_url,
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
            # Delete old image if it exists
            old_data = doc.to_dict()
            old_url = old_data.get("image_url", "")
            if old_url and "firebasestorage" in old_url:
                try:
                    # Extract blob path from url roughly
                    old_path = old_url.split("/o/")[1].split("?")[0].replace("%2F", "/")
                    bucket.blob(old_path).delete()
                except: pass
                
            img_bytes, ext, content_type = process_image(uploaded_file)
            if img_bytes:
                filename = f"models/{uuid.uuid4().hex}.{ext}"
                blob = bucket.blob(filename)
                blob.upload_from_string(img_bytes, content_type=content_type)
                blob.make_public()
                data["image_url"] = blob.public_url
                
        doc_ref.update(data)
    else:
        models = _load_local()
        for m in models:
            if m["id"] == model_id:
                m["title"] = title
                m["description"] = description
                if uploaded_file:
                    if m.get("image_url") and os.path.exists(m["image_url"]):
                        try: os.remove(m["image_url"])
                        except: pass
                    m["image_url"] = _save_local_image(uploaded_file)
                break
        _save_local(models)

def delete_model(model_id):
    if USE_FIREBASE:
        doc_ref = db.collection('models').document(model_id)
        doc = doc_ref.get()
        if doc.exists:
            old_url = doc.to_dict().get("image_url", "")
            if old_url and "firebasestorage" in old_url:
                try:
                    old_path = old_url.split("/o/")[1].split("?")[0].replace("%2F", "/")
                    bucket.blob(old_path).delete()
                except: pass
            doc_ref.delete()
    else:
        models = _load_local()
        for m in models:
            if m["id"] == model_id:
                if m.get("image_url") and os.path.exists(m["image_url"]):
                    try: os.remove(m["image_url"])
                    except: pass
                break
        models = [m for m in models if m["id"] != model_id]
        _save_local(models)
