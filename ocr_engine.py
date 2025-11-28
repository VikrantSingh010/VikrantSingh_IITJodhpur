import io
import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image, UnidentifiedImageError
import pytesseract
import requests

SUPPORTED_IMAGE_EXTS = ("jpg", "jpeg", "png", "webp", "tiff", "bmp", "jfif")

# ---------- Network Download ----------
def download_document(url: str) -> bytes:
    headers = {"User-Agent": "BillExtractor/1.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.content

# ---------- PDF → Images (faster settings) ----------
def pdf_to_images(pdf_bytes: bytes):
    return convert_from_bytes(
        pdf_bytes,
        dpi=220,         
        fmt="jpeg",
        thread_count=4    # use multiple cores if available
    )

# ---------- Preprocess for OCR (speed + accuracy) ----------
def preprocess(img: Image.Image):
    # downscale to speed up Tesseract
    img = img.resize((img.width // 2, img.height // 2))

    arr = np.array(img)
    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)

    # sharpen text
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)

    # binarize
    thresh = cv2.threshold(
        sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return Image.fromarray(thresh)

# ---------- OCR Wrapper ----------
def extract_text_from_image(img: Image.Image) -> str:
    clean = preprocess(img)
    return pytesseract.image_to_string(clean, lang="eng")

# ---------- Universal loader: pdf + any image ----------
def load_document_as_images(url) -> list:
    """
    - url: string URL (pdf or any image type)
    - returns: list[Image.Image]
    Supports pdf, jpg, jpeg, png, webp, tiff, bmp, jfif and more.
    For unknown binary, tries Pillow; if fails → ValueError.
    """
    url = str(url)
    data = download_document(url)

    # detect PDF using header or extension
    if data[:4] == b"%PDF" or url.lower().endswith(".pdf"):
        return pdf_to_images(data)

    # detect by extension
    ext = url.lower().split(".")[-1]
    try_as_image = ext in SUPPORTED_IMAGE_EXTS

    # try image decode
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return [img]
    except UnidentifiedImageError:
        if try_as_image:
            raise ValueError(f"Unsupported image format for URL: {url}")
        # non-image, non-pdf (e.g. txt/json/html) – nothing to OCR
        # caller can decide how to handle this case
        raise ValueError("Downloaded file is neither PDF nor image; cannot OCR.")
