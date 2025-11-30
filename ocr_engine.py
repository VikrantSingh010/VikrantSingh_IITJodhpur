import io
import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image, UnidentifiedImageError
import pytesseract
import requests
from typing import List, Tuple
import hashlib

SUPPORTED_IMAGE_EXTS = ("jpg", "jpeg", "png", "webp", "tiff", "bmp", "jfif")

# ---------- Document Download ----------
def download_document(url: str) -> Tuple[bytes, str]:
    """Download document and return content + content-type"""
    headers = {"User-Agent": "BillExtractor/1.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    content_type = r.headers.get("content-type", "").lower()
    return r.content, content_type

# ---------- PDF → Images ----------
def pdf_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert PDF to images with optimized DPI"""
    return convert_from_bytes(
        pdf_bytes,
        dpi=250,  
        fmt="jpeg",
        thread_count=4,
        grayscale=False  
    )

# ----------Preprocessing ----------
def preprocess_for_ocr(img: Image.Image, aggressive: bool = False) -> Image.Image:
    """
    Multi-stage preprocessing for optimal OCR accuracy
    aggressive=True applies stronger filters for low-quality scans
    """
   
    arr = np.array(img)
    
    if arr.shape[1] > 4000:
        scale = 3000 / arr.shape[1]
        new_width = int(arr.shape[1] * scale)
        new_height = int(arr.shape[0] * scale)
        arr = cv2.resize(arr, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # Convert to grayscale
    if len(arr.shape) == 3:
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    else:
        gray = arr
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # Apply adaptive thresholding
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    
    if aggressive:
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Sharpen text edges
    kernel_sharpen = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ])
    sharpened = cv2.filter2D(binary, -1, kernel_sharpen)
    
    return Image.fromarray(sharpened)

# ---------- Dual OCR Strategy ----------
def extract_text_from_image(img: Image.Image) -> str:
    """
    Try multiple OCR configurations and return best result
    """
    # Standard preprocessing
    clean1 = preprocess_for_ocr(img, aggressive=False)
    text1 = pytesseract.image_to_string(clean1, lang="eng", config='--psm 6')
    
    # For low Quality scans
    clean2 = preprocess_for_ocr(img, aggressive=True)
    text2 = pytesseract.image_to_string(clean2, lang="eng", config='--psm 4')
    
    
    result = text1 if len(text1) > len(text2) else text2
    
    
    if len(result.strip()) < 50:
        text3 = pytesseract.image_to_string(img, lang="eng")
        result = text3 if len(text3) > len(result) else result
    
    return result

# ---------- Document Loading with Type Detection ----------
def load_document_as_images(url: str) -> List[Image.Image]:
    """
    Download and convert document to images
    Handles: PDFs, direct images, and embedded image URLs
    """
    url = str(url).strip()
    
    try:
        data, content_type = download_document(url)
    except Exception as e:
        raise ValueError(f"Failed to download document from {url}: {str(e)}")
    
    # Detect PDF
    if "pdf" in content_type or data[:4] == b"%PDF":
        try:
            return pdf_to_images(data)
        except Exception as e:
            raise ValueError(f"Failed to convert PDF to images: {str(e)}")
    
    # Detect image by content-type or file extension
    url_lower = url.lower()
    is_image_ext = any(url_lower.endswith(f".{ext}") for ext in SUPPORTED_IMAGE_EXTS)
    is_image_content = any(img_type in content_type for img_type in ["image/", "jpg", "jpeg", "png"])
    
    if is_image_ext or is_image_content:
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            return [img]
        except UnidentifiedImageError:
            raise ValueError(f"File appears to be image but cannot be opened: {url}")
    
    
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return [img]
    except Exception:
        raise ValueError(f"Downloaded file is neither PDF nor valid image format: {url}")

# ---------- Image Fingerprinting for Duplicate Detection ----------
def get_image_hash(img: Image.Image) -> str:
    """Generate perceptual hash for duplicate detection"""
    # Resize to standard size for comparison
    small = img.resize((8, 8), Image.LANCZOS).convert('L')
    pixels = list(small.getdata())
    avg = sum(pixels) / len(pixels)
    bits = ''.join('1' if p > avg else '0' for p in pixels)
    return bits

def are_images_similar(hash1: str, hash2: str, threshold: int = 5) -> bool:
    """Check if two image hashes are similar (within threshold Hamming distance)"""
    if len(hash1) != len(hash2):
        return False
    distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    return distance <= threshold
