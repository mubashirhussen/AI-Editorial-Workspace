import io
import re
import hashlib
from typing import Dict, Any, Optional

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB limit

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".markdown",
    ".csv", ".json", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"
}

BLOCKED_BINARY_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".zip", ".tar", ".gz",
    ".bz2", ".7z", ".rar", ".iso", ".dmg", ".pkg", ".deb", ".rpm",
    ".apk", ".jar", ".class", ".pyc", ".pyd", ".bat", ".cmd", ".ps1", ".sh"
}

def normalize_text(text: str) -> str:
    """Normalizes whitespace and removes null bytes or unprintable characters."""
    if not text:
        return ""
    # Strip null bytes and non-printable control characters except standard whitespace
    cleaned = text.replace("\x00", "")
    # Normalize unicode spaces and repeated blank lines
    cleaned = re.sub(r'\r\n|\r', '\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def extract_from_bytes(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts text, metadata, and SHA-256 content hash from uploaded file bytes.
    Enforces a strict 10MB limit and validates file extensions.
    """
    if not file_bytes:
        return {"success": False, "error": "Uploaded file is empty."}

    # 1. Enforce 10 MB payload limit
    if len(file_bytes) > MAX_FILE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        return {
            "success": False,
            "error": f"File exceeds maximum allowed size of 10 MB (received {size_mb:.2f} MB)."
        }

    fn_lower = filename.lower()
    ext = ("." + fn_lower.rsplit(".", 1)[-1]) if "." in fn_lower else ""

    # 2. Reject known unsupported binary formats
    if ext in BLOCKED_BINARY_EXTENSIONS:
        return {
            "success": False,
            "error": f"Unsupported binary format '{ext}'. Supported formats: PDF, DOCX, TXT, MD, CSV, JSON, PNG, JPG, WEBP."
        }

    clean_title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

    # 3. PDF Documents
    if fn_lower.endswith(".pdf") or (content_type and "pdf" in content_type):
        if not file_bytes[:1024].startswith(b"%PDF-") and b"%PDF-" not in file_bytes[:1024]:
            return {
                "success": False,
                "error": "Corrupt or invalid file signature: Expected a valid PDF document (%PDF- magic header missing)."
            }
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt and txt.strip():
                    pages_text.append(f"--- Page {i + 1} ---\n{normalize_text(txt)}")
            content = "\n\n".join(pages_text)
            if not content.strip():
                content = f"[PDF Document '{filename}' with {len(reader.pages)} pages: scanned or image-only PDF]"
            
            normalized = normalize_text(content)
            content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            return {
                "success": True,
                "title": clean_title,
                "content": normalized,
                "source_type": "PDF",
                "page_count": len(reader.pages),
                "content_hash": content_hash,
                "word_count": len(normalized.split()),
                "char_count": len(normalized),
                "mime_type": "application/pdf"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to parse PDF document: {str(e)}"}

    # 4. Word Documents (.docx)
    if fn_lower.endswith(".docx") or (content_type and "wordprocessingml" in content_type):
        if not file_bytes[:4].startswith(b"PK\x03\x04"):
            return {
                "success": False,
                "error": "Corrupt or invalid file signature: Expected a valid DOCX document (PK zip magic header missing)."
            }
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [normalize_text(p.text) for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)
            content = "\n\n".join(paragraphs) or f"[Word Document '{filename}']"
            normalized = normalize_text(content)
            content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            return {
                "success": True,
                "title": clean_title,
                "content": normalized,
                "source_type": "DOCUMENT",
                "content_hash": content_hash,
                "word_count": len(normalized.split()),
                "char_count": len(normalized),
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to parse Word document: {str(e)}"}

    # 5. Images (.png, .jpg, .jpeg, .webp)
    if any(fn_lower.endswith(e) for e in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]):
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            w, h = img.size
            format_name = img.format or "Image"
            content = f"[Visual Source: {filename} ({format_name}, {w}x{h} px)]\nVisual media evidence attached to research investigation."
            
            # OCR if available
            try:
                import pytesseract
                ocr_text = pytesseract.image_to_string(img).strip()
                if ocr_text:
                    content += f"\n\nExtracted OCR Text:\n{ocr_text}"
            except Exception:
                pass

            normalized = normalize_text(content)
            content_hash = hashlib.sha256(file_bytes).hexdigest()
            return {
                "success": True,
                "title": clean_title,
                "content": normalized,
                "source_type": "IMAGE",
                "content_hash": content_hash,
                "word_count": len(normalized.split()),
                "char_count": len(normalized),
                "mime_type": f"image/{format_name.lower()}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to process image: {str(e)}"}

    # 6. Text, Markdown, CSV, JSON
    try:
        decoded = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            decoded = file_bytes.decode("latin-1")
        except Exception as e:
            return {"success": False, "error": f"Could not decode text file content: {str(e)}"}

    normalized = normalize_text(decoded)
    content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return {
        "success": True,
        "title": clean_title,
        "content": normalized,
        "source_type": "TEXT",
        "content_hash": content_hash,
        "word_count": len(normalized.split()),
        "char_count": len(normalized),
        "mime_type": "text/plain"
    }
