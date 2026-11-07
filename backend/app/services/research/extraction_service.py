import hashlib
import httpx
import logging
import ipaddress
import socket
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, Optional
import trafilatura
from bs4 import BeautifulSoup
from backend.app.core.config import settings
from backend.app.utils.security import is_safe_url

logger = logging.getLogger(__name__)


def canonicalize_url(url: str) -> str:
    """Strips tracking parameters and trailing slashes for stable canonical URL representation."""
    if not url:
        return ""
    try:
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
        parsed = urlparse(url.strip())
        # Filter tracking query parameters
        filtered_queries = [
            (k, v) for k, v in parse_qsl(parsed.query)
            if not k.lower().startswith("utm_") and k.lower() not in ("ref", "fbclid", "gclid", "mc_cid", "mc_eid")
        ]
        new_query = urlencode(filtered_queries)
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.params, new_query, ""))
    except Exception:
        return url.strip()

class ResearchExtractionService:
    """
    Robust, secure content extraction engine.
    Implements SSRF defense, per-redirect hop validation, payload bounds,
    and a dual-layer Trafilatura + BeautifulSoup extraction pipeline.
    """

    def validate_url(self, url: str) -> Optional[str]:
        """Validates that a URL is HTTP/HTTPS and passes SSRF checks."""
        if not url or not isinstance(url, str):
            return "URL cannot be empty."
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in ("http", "https"):
            return f"Invalid protocol '{parsed.scheme}'. Only HTTP and HTTPS URLs are accepted."
        if not is_safe_url(url.strip()):
            return "Security violation: Access to localhost, private IP subnets, or internal addresses is blocked."
        return None

    async def extract_url(self, url: str) -> Dict[str, Any]:
        """
        Extracts content from a URL with defense-in-depth security.
        """
        url_err = self.validate_url(url)
        if url_err:
            return {
                "success": False,
                "error": url_err,
                "title": "",
                "content": "",
                "author": None,
                "published_at": None,
                "canonical_url": url,
                "extraction_status": "failed"
            }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        current_url = url.strip()
        max_redirects = getattr(settings, "MAX_REDIRECTS", 4)
        timeout_seconds = getattr(settings, "EXTRACTION_TIMEOUT_SECONDS", 12.0)
        max_bytes = getattr(settings, "MAX_EXTRACTION_BYTES", 2_000_000)

        raw_html = ""
        final_canonical = current_url

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, verify=True) as client:
                for redirect_hop in range(max_redirects + 1):
                    # Validate SSRF on every redirect destination
                    hop_err = self.validate_url(current_url)
                    if hop_err:
                        return {
                            "success": False,
                            "error": f"Redirect destination blocked: {hop_err}",
                            "title": "",
                            "content": "",
                            "author": None,
                            "published_at": None,
                            "canonical_url": current_url,
                            "extraction_status": "failed"
                        }

                    resp = await client.get(current_url, headers=headers, follow_redirects=False)

                    if resp.is_redirect:
                        location = resp.headers.get("Location")
                        if not location:
                            break
                        current_url = urljoin(current_url, location)
                        continue

                    # Final non-redirect response reached
                    final_canonical = str(resp.url)
                    if resp.status_code != 200:
                        return {
                            "success": False,
                            "error": f"HTTP {resp.status_code}: Website returned an error ({resp.reason_phrase}).",
                            "title": "",
                            "content": "",
                            "author": None,
                            "published_at": None,
                            "canonical_url": final_canonical,
                            "extraction_status": "failed"
                        }

                    content_type = resp.headers.get("content-type", "").lower()
                    if content_type and ("application/pdf" in content_type or current_url.lower().endswith(".pdf")):
                        try:
                            from backend.app.services.research.document_extractor import extract_from_bytes
                            pdf_data = extract_from_bytes(resp.content, current_url.split("/")[-1] or "document.pdf", content_type)
                            if pdf_data.get("success"):
                                return {
                                    "success": True,
                                    "error": None,
                                    "title": pdf_data.get("title") or "PDF Document",
                                    "content": pdf_data.get("content", ""),
                                    "author": None,
                                    "published_at": None,
                                    "canonical_url": final_canonical,
                                    "extraction_status": "completed"
                                }
                        except Exception as e:
                            logger.warning(f"PDF extraction fallback: {e}")
                    elif content_type and any(t in content_type for t in ["text/plain", "text/markdown", "application/json"]):
                        raw_text = resp.text
                        if len(raw_text.encode("utf-8")) > max_bytes:
                            raw_text = raw_text[:max_bytes]
                        clean_title = current_url.split("/")[-1].replace("-", " ").replace("_", " ").title()
                        return {
                            "success": True,
                            "error": None,
                            "title": clean_title or f"Document from {urlparse(final_canonical).netloc}",
                            "content": raw_text.strip(),
                            "author": None,
                            "published_at": None,
                            "canonical_url": final_canonical,
                            "extraction_status": "completed"
                        }

                    raw_html = resp.text
                    if len(raw_html.encode("utf-8")) > max_bytes:
                        raw_html = raw_html[:max_bytes]
                    break

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Connection timed out. The remote website took too long to respond.",
                "title": "",
                "content": "",
                "author": None,
                "published_at": None,
                "canonical_url": current_url,
                "extraction_status": "failed"
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Network error connecting to website: {str(e)}",
                "title": "",
                "content": "",
                "author": None,
                "published_at": None,
                "canonical_url": current_url,
                "extraction_status": "failed"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected extraction error: {str(e)}",
                "title": "",
                "content": "",
                "author": None,
                "published_at": None,
                "canonical_url": current_url,
                "extraction_status": "failed"
            }

        # Parsing: Trafilatura primary
        trafilatura_extracted = None
        trafilatura_metadata = None
        try:
            trafilatura_extracted = trafilatura.extract(
                raw_html,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            trafilatura_metadata = trafilatura.extract_metadata(raw_html)
        except Exception:
            pass

        title = ""
        author = None
        published_at = None

        if trafilatura_metadata:
            title = trafilatura_metadata.title or ""
            author = trafilatura_metadata.author
            published_at = trafilatura_metadata.date

        # Fallback to BeautifulSoup DOM inspection for metadata & body
        soup = BeautifulSoup(raw_html, "html.parser")

        if not title:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()
            else:
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text().strip()

        if not author:
            author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
            if author_meta and author_meta.get("content"):
                author = author_meta["content"].strip()

        if not published_at:
            time_meta = soup.find("meta", property="article:published_time") or soup.find("meta", attrs={"name": "publication_date"})
            if time_meta and time_meta.get("content"):
                published_at = time_meta["content"].strip()

        final_content = trafilatura_extracted
        if not final_content or len(final_content.strip()) < 100:
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form", "svg"]):
                tag.extract()
            main_element = soup.find("article") or soup.find("main") or soup.find("div", class_=lambda c: c and any(x in str(c).lower() for x in ["content", "post", "article", "entry"]))
            if main_element:
                paragraphs = [p.get_text().strip() for p in main_element.find_all("p")]
                final_content = "\n\n".join([p for p in paragraphs if len(p) > 20])
            else:
                paragraphs = [p.get_text().strip() for p in soup.find_all("p")]
                final_content = "\n\n".join([p for p in paragraphs if len(p) > 20])

        if not final_content or len(final_content.strip()) < 50:
            meta_desc = (soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description"))
            desc_text = meta_desc.get("content", "").strip() if meta_desc else ""
            heading_texts = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3", "li"]) if len(h.get_text().strip()) > 10]
            
            combined = []
            if title:
                combined.append(f"Title: {title}")
            if desc_text:
                combined.append(f"Overview: {desc_text}")
            if heading_texts:
                combined.append("Key Sections and Topics:\n" + "\n".join(f"- {h}" for h in heading_texts[:15]))
                
            fallback_text = "\n\n".join(combined)
            if len(fallback_text.strip()) >= 30:
                final_content = fallback_text

        if not final_content or len(final_content.strip()) < 30:
            path_words = [w for w in urlparse(final_canonical).path.split("/") if w and not w.isdigit()]
            derived_title = title or (" ".join(path_words[-2:]).replace("-", " ").title() if path_words else "Web Article")
            final_content = f"Source Document: {derived_title}\nReference URL: {final_canonical}\nRemote site returned limited static text content. Overview derived from page headers and metadata."
            title = derived_title

        if not title:
            domain = urlparse(final_canonical).netloc or "Web Source"
            title = f"Article from {domain}"

        clean_body = final_content.strip()
        c_hash = hashlib.sha256(clean_body.encode("utf-8")).hexdigest()
        c_url = canonicalize_url(final_canonical)
        return {
            "success": True,
            "error": None,
            "title": title,
            "content": clean_body,
            "author": author,
            "published_at": published_at,
            "canonical_url": c_url,
            "content_hash": c_hash,
            "word_count": len(clean_body.split()),
            "char_count": len(clean_body),
            "domain": urlparse(c_url).netloc,
            "extraction_status": "completed"
        }

    def process_pasted_text(self, text: str, user_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates and processes manually pasted text content.
        """
        clean_text = (text or "").strip()
        if len(clean_text) < 10:
            return {
                "success": False,
                "error": "Pasted text is too short. Please provide at least 10 characters.",
                "title": "",
                "content": "",
                "extraction_status": "failed"
            }

        title = (user_title or "").strip()
        if not title:
            first_line = clean_text.split("\n")[0].strip()
            words = first_line.split()[:8]
            title = " ".join(words) + ("..." if len(first_line.split()) > 8 else "")
            if not title:
                title = "Pasted Technical Document"

        c_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        return {
            "success": True,
            "error": None,
            "title": title,
            "content": clean_text,
            "content_hash": c_hash,
            "word_count": len(clean_text.split()),
            "char_count": len(clean_text),
            "domain": "pasted_text",
            "extraction_status": "completed"
        }

extraction_service = ResearchExtractionService()
