import streamlit as st
import database as db

st.set_page_config(page_title="Change Makers 8c", page_icon="🏛️", layout="wide")

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
    # Display in a grid
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
