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

# Upload PDFs
uploaded_files = st.file_uploader("Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

def create_thumbnail_from_pdf(pdf_bytes, index):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap()
        image = Image.open(io.BytesIO(pix.tobytes("ppm")))

        # Resize image to fixed height
        max_height = 100
        aspect_ratio = image.width / image.height
        new_width = int(max_height * aspect_ratio)
        image = image.resize((new_width, max_height))

        # Save to disk
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

            # Excel column width: 1 unit ≈ 7 pixels
            col_width_units = img_width / 7.0
            row_height_points = img_height * 0.75

            worksheet.set_column(col, col, col_width_units)
            worksheet.set_row(row, row_height_points)

            # Calculate x/y scale so image fits perfectly in cell
            with Image.open(image_path) as img:
                orig_width, orig_height = img.size

            x_scale = img_width / orig_width
            y_scale = img_height / orig_height

            worksheet.insert_image(row, col, image_path, {
                'x_scale': x_scale,
                'y_scale': y_scale,
                'object_position': 1  # Move and size with cells
            })

            col += 1

        workbook.close()
        shutil.rmtree(TEMP_DIR)

        st.success("✅ Excel file generated with thumbnails embedded in cells!")
        st.download_button(
            label="📥 Download Excel File",
            data=output.getvalue(),
            file_name="pdf_thumbnails.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
