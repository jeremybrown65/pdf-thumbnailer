import streamlit as st
import io
import zipfile
import os
import shutil
from PIL import Image

# PDF-to-image (requires PyMuPDF for Streamlit compatibility)
import fitz  # PyMuPDF

# Excel creation
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage

# Cleanup any previous temp folders
def clear_temp_folders():
    for folder in ["temp_pdfs", "resized_thumbnails"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

clear_temp_folders()

st.set_page_config(page_title="PDF Tools", layout="centered")
st.title("📁 PDF Tools – Thumbnails + Excel")

# Tabs
tab1, tab2 = st.tabs(["🖼️ Generate Thumbnails", "📊 Thumbnails to Excel"])

# =================== TAB 1 =====================
with tab1:
    st.header("Generate JPEG Thumbnails from PDFs")
    uploaded_pdfs = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True)

    def create_pdf_thumbnail(pdf_bytes, filename):
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap()
            image = Image.open(io.BytesIO(pix.tobytes("ppm")))

            aspect_ratio = image.width / image.height
            new_width = int(200 * aspect_ratio)
            image = image.resize((new_width, 200))

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="JPEG")
            return filename.replace(".pdf", ".jpg"), img_byte_arr.getvalue()
        except Exception as e:
            st.error(f"Error processing {filename}: {e}")
            return None, None

    if uploaded_pdfs:
        with st.spinner("Generating thumbnails..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
                for uploaded_file in uploaded_pdfs:
                    filename = uploaded_file.name
                    file_bytes = uploaded_file.read()
                    img_name, img_data = create_pdf_thumbnail(file_bytes, filename)
                    if img_name:
                        zipf.writestr(img_name, img_data)

            st.success("Thumbnails generated!")
            st.download_button(
                label="📥 Download Thumbnails ZIP",
                data=zip_buffer.getvalue(),
                file_name="thumbnails.zip",
                mime="application/zip"
            )

# =================== TAB 2 =====================
with tab2:
    st.header("Insert Thumbnails into Excel Row")
    uploaded_images = st.file_uploader("Upload image files (JPEG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_images:
        wb = Workbook()
        ws = wb.active
        ws.title = "Thumbnails"

        os.makedirs("resized_thumbnails", exist_ok=True)

        for i, uploaded_file in enumerate(uploaded_images):
            img_data = uploaded_file.read()
            image = Image.open(io.BytesIO(img_data))

            # Resize to 100px height
            aspect_ratio = image.width / image.height
            new_height = 100
            new_width = int(new_height * aspect_ratio)
            image = image.resize((new_width, new_height))

            # Save temp PNG
            temp_path = f"resized_thumbnails/img_{i}.png"
            image.save(temp_path, format="PNG")

            # Insert into Excel
            img = XLImage(temp_path)
            col_letter = chr(65 + i)
            ws.column_dimensions[col_letter].width = new_width // 7
            ws.row_dimensions[1].height = new_height * 0.75
            ws.add_image(img, f"{col_letter}1")

        # Save Excel in memory
        output = io.BytesIO()
        wb.save(output)
        clear_temp_folders()

        st.success("Excel created!")
        st.download_button(
            label="📥 Download Excel File",
            data=output.getvalue(),
            file_name="thumbnails.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
