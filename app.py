def generate_thumbnail(pdf_bytes, original_filename):
    try:
        # Skip likely invalid macOS files
        if original_filename.startswith("._") or len(pdf_bytes) < 1024:
            raise ValueError("Skipped: Not a valid PDF (likely macOS resource file).")

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
        st.warning(f"⚠️ Skipped '{original_filename}': {e}")
        return None
