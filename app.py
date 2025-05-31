import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import zipfile
import os
import shutil

# Setup
st.set_page_config(page_title="PDF Thumbnail Generator", layout="centered")
st.title("📄 PDF Thumbnail Generator")

# Cleanup
TEMP_DIR = "thumbnails_temp"
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR, exist_ok=True)

# Upload PDFs
uploaded_files = st.file_uploader("Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

def generate_thumbnail(pdf_bytes, index):
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

        img_path = f"{TEMP_DIR}/thumb_{index+1}.jpg"
        image.save(img_path, format="JPEG")
        return img_path
    except Exception as e:
        st.error(f"Error processing PDF #{index+1}: {e}")
        return None

if uploaded_files:
    with st.spinner("Generating thumbnails..."):
        image_paths = []

        for i, file in enumerate(uploaded_files):
            pdf_data = file.read()
            img_path = generate_thumbnail(pdf_data, i)
            if img_path:
                image_paths.append(img_path)

        # Package into ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for img_path in image_paths:
                filename = os.path.basename(img_path)
                with open(img_path, "rb") as f:
                    zipf.writestr(filename, f.read())

        # Cleanup temp images
        shutil.rmtree(TEMP_DIR)

        st.success("✅ Thumbnails generated!")
        st.download_button(
            label="📥 Download Thumbnails (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="pdf_thumbnails.zip",
            mime="application/zip"
        )
