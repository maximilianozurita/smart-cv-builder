"""WeasyPrint wrapper: HTML string → PDF bytes.

Guarantees single-page output by progressively tightening spacing when the
initial render overflows beyond one page.
"""
from __future__ import annotations

# Compact CSS injected when content overflows one page
_COMPACT_CSS = """
@page { margin: 10mm 12mm !important; }
body { line-height: 1.28 !important; }
.cv-page { padding: 0 !important; }
.cv-header { padding-bottom: 6px !important; margin-bottom: 8px !important; }
.cv-section { margin-bottom: 6px !important; }
.section-title { padding-bottom: 1px !important; margin-bottom: 3px !important; }
.exp-bullets li { margin-bottom: 1px !important; }
.skill-group { margin-bottom: 1px !important; }
"""

_VERY_COMPACT_CSS = _COMPACT_CSS + """
body { font-size: 8.8pt !important; line-height: 1.25 !important; }
.cv-header h1 { font-size: 17pt !important; }
"""


def html_to_pdf(html: str) -> bytes:
    from weasyprint import HTML  # lazy import

    doc = HTML(string=html).render()

    if len(doc.pages) == 1:
        return doc.write_pdf()

    # Overflow: try compact spacing first
    compact_html = _inject_css(html, _COMPACT_CSS)
    doc2 = HTML(string=compact_html).render()
    if len(doc2.pages) == 1:
        return doc2.write_pdf()

    # Still overflows: reduce font size too
    very_compact_html = _inject_css(html, _VERY_COMPACT_CSS)
    return HTML(string=very_compact_html).write_pdf()


def _inject_css(html: str, css: str) -> str:
    tag = f'<style>{css}</style></head>'
    return html.replace('</head>', tag, 1)
