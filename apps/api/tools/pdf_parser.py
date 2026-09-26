import io
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts text from PDF binary stream in memory without writing to disk (Invariant 2 & 4)."""
    if not pdf_bytes:
        return ""

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages = []
        for _i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text)
        return "\n\n".join(extracted_pages)
    except Exception as e:
        logger.error(f"Failed to extract text from in-memory PDF: {e}")
        return ""
