import json
import re
import html
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.models.base import EditorialOutput
from backend.app.schemas.editorial import EditorialExportResponse

class ExportService:
    """
    Exports saved editorial outputs into Markdown, Plain Text, semantic HTML5, and structured JSON formats.
    """

    def export(self, editorial: EditorialOutput, format_type: str = "markdown") -> EditorialExportResponse:
        fmt = (format_type or "markdown").lower().strip()
        now = datetime.now(timezone.utc)

        # Build Markdown
        md_content = self.build_markdown(editorial)

        # Build Plain Text
        plain_text = self.build_plain_text(editorial)

        # Build HTML5
        html_content = self.build_html(editorial)

        # Build JSON
        json_content = self.build_json(editorial, exported_at=now)

        return EditorialExportResponse(
            editorial_id=editorial.id,
            headline=editorial.headline,
            markdown_content=md_content,
            plain_text_content=plain_text,
            html_content=html_content,
            json_content=json_content,
            format=fmt,
            word_count=editorial.word_count,
            exported_at=now
        )

    def build_json(self, editorial: EditorialOutput, exported_at: datetime) -> str:
        data = {
            "id": editorial.id,
            "project_id": editorial.project_id,
            "headline": editorial.headline,
            "content": editorial.content,
            "word_count": editorial.word_count,
            "status": editorial.status,
            "source_references": editorial.source_references or [],
            "ai_review_results": editorial.ai_review_results or {},
            "version": getattr(editorial, "version", 1),
            "created_at": editorial.created_at.isoformat() if editorial.created_at else None,
            "updated_at": editorial.updated_at.isoformat() if editorial.updated_at else None,
            "exported_at": exported_at.isoformat()
        }
        return json.dumps(data, indent=2)

    def build_markdown(self, editorial: EditorialOutput) -> str:
        lines = [
            f"# {editorial.headline}\n",
            f"*Published via This Week in AI Editorial Workspace* | *Word Count: {editorial.word_count} words*\n",
            editorial.content.strip(),
            "\n## References & Verified Sources\n"
        ]

        if editorial.source_references:
            for s in editorial.source_references:
                idx = s.get("index", 1)
                title = s.get("title", s.get("source_title", "Source Document"))
                url = s.get("url", s.get("source_url", "#"))
                claim = s.get("supported_claim", s.get("citation_text", ""))
                lines.append(f"[{idx}] [{title}]({url}) — *{claim}*")
        else:
            lines.append("No explicit source references indexed.")

        return "\n".join(lines)

    def build_plain_text(self, editorial: EditorialOutput) -> str:
        lines = [
            editorial.headline.upper(),
            "=" * len(editorial.headline),
            f"Word Count: {editorial.word_count} words\n",
            editorial.content.strip(),
            "\n" + "-" * 40,
            "REFERENCES & SOURCES:"
        ]

        if editorial.source_references:
            for s in editorial.source_references:
                idx = s.get("index", 1)
                title = s.get("title", s.get("source_title", "Source Document"))
                url = s.get("url", s.get("source_url", "N/A"))
                lines.append(f"[{idx}] {title} ({url})")
        else:
            lines.append("No explicit source references indexed.")

        return "\n".join(lines)

    def build_html(self, editorial: EditorialOutput) -> str:
        # Convert markdown-style paragraphs and subheads into semantic HTML with XSS sanitization
        headline_escaped = html.escape(editorial.headline or "Editorial Article")
        body_html = ""
        paragraphs = (editorial.content or "").strip().split("\n\n")
        
        for p in paragraphs:
            clean_p = p.strip()
            if not clean_p:
                continue
            if clean_p.startswith("### "):
                safe_heading = html.escape(clean_p[4:])
                body_html += f"<h3>{safe_heading}</h3>\n"
            elif clean_p.startswith("## "):
                safe_heading = html.escape(clean_p[3:])
                body_html += f"<h2>{safe_heading}</h2>\n"
            elif clean_p.startswith("# "):
                safe_heading = html.escape(clean_p[2:])
                body_html += f"<h1>{safe_heading}</h1>\n"
            else:
                # Escape user content before wrapping citations
                safe_p = html.escape(clean_p)
                formatted_p = re.sub(r"\[(\d+)\]", r'<sup class="citation">[\1]</sup>', safe_p)
                body_html += f"<p>{formatted_p}</p>\n"

        refs_html = ""
        if editorial.source_references:
            refs_html += '<ol class="editorial-references">\n'
            for s in editorial.source_references:
                raw_title = s.get("title", s.get("source_title", "Source Document"))
                raw_url = s.get("url", s.get("source_url", "#"))
                raw_claim = s.get("supported_claim", s.get("citation_text", ""))
                safe_title = html.escape(str(raw_title))
                raw_url_str = str(raw_url).strip()
                if raw_url_str.lower().startswith(("http://", "https://", "#")):
                    safe_url = html.escape(raw_url_str, quote=True)
                else:
                    safe_url = "#"
                safe_claim = html.escape(str(raw_claim))
                refs_html += f'  <li><a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_title}</a> — <em>{safe_claim}</em></li>\n'
            refs_html += '</ol>\n'
        else:
            refs_html = "<p><em>No external source references indexed.</em></p>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{headline_escaped}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: #1e293b;
      max-width: 720px;
      margin: 40px auto;
      padding: 0 20px;
    }}
    h1 {{ font-size: 2rem; color: #0f172a; margin-bottom: 0.5rem; }}
    h2 {{ font-size: 1.4rem; color: #1e293b; margin-top: 2rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3rem; }}
    h3 {{ font-size: 1.1rem; color: #334155; margin-top: 1.5rem; }}
    p {{ margin-bottom: 1.25rem; font-size: 1.05rem; }}
    .meta {{ font-size: 0.85rem; color: #64748b; margin-bottom: 2rem; }}
    sup.citation {{ color: #2563eb; font-weight: bold; margin-left: 2px; }}
    .editorial-references {{ font-size: 0.9rem; color: #475569; padding-left: 1.5rem; }}
    .editorial-references a {{ color: #2563eb; text-decoration: none; }}
    .editorial-references a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>{headline_escaped}</h1>
  <div class="meta">Published via This Week in AI Editorial Workspace &bull; {editorial.word_count} words</div>
  <article>
{body_html}
  </article>
  <hr style="margin-top: 3rem; border: none; border-top: 1px solid #e2e8f0;" />
  <h2>References & Verified Sources</h2>
{refs_html}
</body>
</html>"""

export_service = ExportService()

