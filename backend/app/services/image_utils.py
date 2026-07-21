import io
from PIL import Image


def optimize_image(
    image_data: bytes,
    max_size: int = 1800,
    quality: int = 85,
    max_file_size_mb: float = 19,
) -> bytes:
    """
    Resize and compress an image so it stays under max_file_size_mb.
    Exact port of the function in streamlit_app_cloud.py.
    Returns original bytes if optimization fails.
    """
    try:
        img = Image.open(io.BytesIO(image_data))

        if not img.format:
            img.format = "JPEG"

        if img.format not in ["JPEG", "JPG", "PNG", "GIF", "BMP", "TIFF", "TIF"]:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.format = "JPEG"

        # Initial resize
        if img.width > max_size or img.height > max_size:
            if img.width >= img.height:
                new_width = max_size
                new_height = int(img.size[1] * (max_size / img.size[0]))
            else:
                new_height = max_size
                new_width = int(img.size[0] * (max_size / img.size[1]))
            img = img.resize((new_width, new_height), Image.LANCZOS)

        current_quality = quality
        current_size = max_size
        buffer = io.BytesIO()

        fmt = img.format or "JPEG"
        if fmt in ("JPEG", "JPG"):
            img.save(buffer, format="JPEG", quality=current_quality, optimize=True)
        elif fmt == "PNG":
            img.save(buffer, format="PNG", optimize=True)
        else:
            img.save(buffer, format=fmt)

        buffer.seek(0)
        current_file_size_mb = len(buffer.getvalue()) / (1024 * 1024)

        attempts = 0
        while current_file_size_mb > max_file_size_mb and attempts < 10:
            attempts += 1
            buffer = io.BytesIO()
            fmt = img.format or "JPEG"

            if current_quality > 15:
                current_quality -= 10
            elif current_size > 800:
                current_size = int(current_size * 0.8)
                if img.width >= img.height:
                    new_width = current_size
                    new_height = int(img.size[1] * (current_size / img.size[0]))
                else:
                    new_height = current_size
                    new_width = int(img.size[0] * (current_size / img.size[1]))
                img = img.resize((new_width, new_height), Image.LANCZOS)
            else:
                if fmt not in ("JPEG", "JPG"):
                    img.format = "JPEG"
                    fmt = "JPEG"
                    current_quality = 60
                else:
                    current_quality = max(10, current_quality - 15)

            if fmt in ("JPEG", "JPG"):
                img.save(buffer, format="JPEG", quality=current_quality, optimize=True)
            elif fmt == "PNG":
                img.save(buffer, format="PNG", optimize=True)
            else:
                img.save(buffer, format=fmt)

            buffer.seek(0)
            current_file_size_mb = len(buffer.getvalue()) / (1024 * 1024)

        return buffer.getvalue()

    except Exception as e:
        print(f"Image optimization error: {e}")
        return image_data


def strip_exif_and_repack(file_bytes: bytes, filename: str) -> bytes:
    """
    Re-save image via PIL to strip EXIF metadata (fixes date ordering in Procore).
    Used for Tab 1 (Procore) uploads only.
    Returns original bytes if it fails.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        buf = io.BytesIO()
        fmt = img.format if img.format else "JPEG"
        img.save(buf, format=fmt)
        return buf.getvalue()
    except Exception:
        return file_bytes
