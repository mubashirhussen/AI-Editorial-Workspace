import io
from typing import Dict, Any, Optional

def extract_from_bytes(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> Dict[str, Any]:
    fn_lower = filename.lower()
    clean_title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

    # 1. PDF Documents
    if fn_lower.endswith(".pdf") or (content_type and "pdf" in content_type):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt and txt.strip():
                    pages_text.append(f"--- Page {i + 1} ---\n{txt.strip()}")
            content = "\n\n".join(pages_text)
            if not content.strip():
                content = f"[PDF Document '{filename}' with {len(reader.pages)} pages: scanned or image-only PDF]"
            return {
                "success": True,
                "title": clean_title,
                "content": content.strip(),
                "source_type": "PDF",
                "page_count": len(reader.pages)
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to parse PDF: {str(e)}"}

    # 2. Word Documents (.docx)
    if fn_lower.endswith(".docx") or (content_type and "wordprocessingml" in content_type):
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)
            content = "\n\n".join(paragraphs)
            return {
                "success": True,
                "title": clean_title,
                "content": content.strip() or f"[Word Document '{filename}']",
                "source_type": "DOCUMENT"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to parse Word document: {str(e)}"}

    # 3. Images (.png, .jpg, .jpeg, .webp)
    if any(fn_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]):
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            w, h = img.size
            format_name = img.format or "Image"
            content = f"[Visual Source: {filename} ({format_name}, {w}x{h} px)]\nVisual media evidence attached to research investigation."
            
            # Check for OCR if available
            try:
                import pytesseract
                ocr_text = pytesseract.image_to_string(img).strip()
                if ocr_text:
                    content += f"\n\nExtracted OCR Text:\n{ocr_text}"
            except Exception:
                pass

            return {
                "success": True,
                "title": clean_title,
                "content": content,
                "source_type": "IMAGE"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to process image: {str(e)}"}

    # 4. Text, Markdown, CSV, JSON
    try:
        decoded = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            decoded = file_bytes.decode("latin-1")
        except Exception as e:
            return {"success": False, "error": f"Could not decode file content: {str(e)}"}

    return {
        "success": True,
        "title": clean_title,
        "content": decoded.strip(),
        "source_type": "TEXT"
    }

print("Extractor prototype compiled successfully")
