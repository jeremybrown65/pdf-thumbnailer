import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import zipfile
import os
import shutil

# --- Setup ---
st.set_page_config(page_title="PDF Thumbnail Generator", layout="centered")
st.title("📄 PDF Thumbnail Generator")

# --- Constants ---
TEMP_DIR = "thumbnails_temp"

# --- Ensure temp folder exists ---
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)

# --- File uploader ---
uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

# --- Convert a PDF to a thumbnail image ---
def generate_thumbnail(pdf_bytes, original_filename):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        image = Image.open(io.BytesIO(pix.tobytes("ppm")))

        # Resize to 200px tall
        target_height = 200
        aspect_ratio = image.width / image.height
        new_width = int(target_height * aspect_ratio)
        image = image.resize((new_width, target_height))

        # Create safe filename
        base_name = os.path.splitext(original_filename)[0]
        safe_name = base_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        img_path = f"{TEMP_DIR}/{safe_name}.jpg"
        image.save(img_path, format="JPEG")

        return img_path
    except Exception as e:
        st.error(f"Error processing '{original_filename}': {e}")
        return None

# --- Process uploaded PDFs ---
if uploaded_files:
    with st.spinner("Generating thumbnails..."):
        image_paths = []

        for file in uploaded_files:
            pdf_data = file.read()
            img_path = generate_thumbnail(pdf_data, file.name)
            if img_path:
                image_paths.append(img_path)

        if image_paths:
            # Package into ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for img_path in image_paths:
                    filename = os.path.basename(img_path)
                    with open(img_path, "rb") as f:
                        zipf.writestr(filename, f.read())

            st.success("✅ Thumbnails generated!")
            st.download_button(
                label="📥 Download Thumbnails (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="pdf_thumbnails.zip",
                mime="application/zip"
            )
        else:
            st.warning("No thumbnails were created.")
