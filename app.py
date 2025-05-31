import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import shutil
import xlsxwriter

# Setup
st.set_page_config(page_title="PDF to Excel Thumbnails", layout="centered")
st.title("📄 PDF to Excel Thumbnail Sheet")

# Cleanup
TEMP_DIR = "resized_thumbnails"
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR, exist_ok=True)

uploaded_files = st.file_uploader("Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

def create_thumbnail_from_pdf(pdf_bytes, index):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        image = Image.open(io.BytesIO(pix.tobytes("ppm")))

        max_height = 100
        aspect_ratio = image.width / image.height
        new_width = int(max_height * aspect_ratio)
        image = image.resize((new_width, max_height))

        path = f"{TEMP_DIR}/thumb_{index}.png"
        image.save(path, format="PNG")

        return path, new_width, max_height
    except Exception as e:
        st.error(f"Error processing PDF #{index+1}: {e}")
        return None, None, None

if uploaded_files:
    with st.spinner("Processing PDFs and generating Excel..."):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Thumbnails")

        row = 0
        col = 0

        for i, uploaded_file in enumerate(uploaded_files):
            file_bytes = uploaded_file.read()
            image_path, img_width, img_height = create_thumbnail_from_pdf(file_bytes, i)
            if not image_path:
                continue

            # Excel units: column width ~7.5px, row height in points (1pt ≈ 1.33px)
            col_width = img_width / 7.5
            row_height = img_height * 0.75

            worksheet.set_column(col, col, col_width)
            worksheet.set_row(row, row_height)

            worksheet.insert_image(row, col, image_path, {
                'x_offset': 0,
                'y_offset': 0,
                'object_position': 1,  # Move and size with cells
                # No scaling needed if column and row exactly match
            })

            col += 1

        workbook.close()
        shutil.rmtree(TEMP_DIR)

        st.success("✅ Excel file generated with thumbnails embedded in resizable cells!")
        st.download_button(
            label="📥 Download Excel File",
            data=output.getvalue(),
            file_name="pdf_thumbnails.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
