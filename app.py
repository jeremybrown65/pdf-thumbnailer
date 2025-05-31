import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image
import zipfile
import io
import os

st.set_page_config(page_title="PDF Thumbnail Generator", layout="centered")

st.title("📄 PDF Thumbnail Generator")
st.write("Upload one or more PDFs to generate JPEG thumbnails (first page, 200px height).")

uploaded_files = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True)

def create_thumbnail(pdf_bytes, filename):
    try:
        pages = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
        page = pages[0]

        aspect_ratio = page.width / page.height
        new_width = int(200 * aspect_ratio)
        page.thumbnail((new_width, 200))
        
        img_byte_arr = io.BytesIO()
        page.save(img_byte_arr, format='JPEG')
        return filename.replace(".pdf", ".jpg"), img_byte_arr.getvalue()
    except Exception as e:
        st.error(f"Error processing {filename}: {e}")
        return None, None

if uploaded_files:
    with st.spinner("Generating thumbnails..."):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
            for uploaded_file in uploaded_files:
                filename = uploaded_file.name
                file_bytes = uploaded_file.read()
                img_name, img_data = create_thumbnail(file_bytes, filename)
                if img_name:
                    zipf.writestr(img_name, img_data)
        
        st.success("Thumbnails generated!")
        st.download_button(
            label="📥 Download All Thumbnails (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="thumbnails.zip",
            mime="application/zip"
        )
