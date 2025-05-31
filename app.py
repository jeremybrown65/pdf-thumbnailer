import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import zipfile
import os
import shutil
from pathlib import Path

# --- Setup ---
st.set_page_config(page_title="PDF Thumbnail Generator", layout="centered")
st.title("📄 Upload PDFs or ZIP of PDFs")

# --- Constants ---
TEMP_PDF_DIR = "pdf_temp"
TEMP_IMG_DIR = "thumbnails_temp"

# --- Clean temp folders ---
for folder in [TEMP_PDF_DIR, TEMP_IMG_DIR]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

# --- Upload options ---
uploaded_pdfs = st.file_uploader("Upload individual PDF files", type=["pdf"], accept_multiple_files=True)
uploaded_zip = st.file_uploader("Or upload a .zip file containing PDFs", type=["zip"])

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
        img_path = f"{TEMP_IMG_DIR}/{safe_name}.jpg"
        image.save(img_path, format="JPEG")

        return img_path
    except Exception as e:
        st.error(f"Error processing '{original_filename}': {e}")
        return None

# --- Collect and process all PDFs ---
all_pdfs = []

# From ZIP
if uploaded_zip:
    with st.spinner("Extracting ZIP..."):
        with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
            zip_ref.extractall(TEMP_PDF_DIR)
        pdf_paths = list(Path(TEMP_PDF_DIR).rglob("*.pdf"))
        for path in pdf_paths:
            all_pdfs.append((path.read_bytes(), path.name))

# From individual uploads
if uploaded_pdfs:
    for file in uploaded_pdfs:
        all_pdfs.append((file.read(), file.name))

# Process if any PDFs were found
if all_pdfs:
    with st.spinner("Generating thumbnails..."):
        image_paths = []

        for pdf_bytes, name in all_pdfs:
            img_path = generate_thumbnail(pdf_bytes, name)
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
else:
    st.info("Upload PDFs or a ZIP file to get started.")
