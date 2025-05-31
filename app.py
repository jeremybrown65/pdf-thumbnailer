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

# --- Ensure clean temp folder ---
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

        # Create safe f
