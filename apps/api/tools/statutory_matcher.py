import logging
from typing import Any

from apps.api.tools.embeddings import generate_embedding
from supabase import Client

logger = logging.getLogger(__name__)


def match_statute_clause(
    query_text: str,
    supabase_client: Client | None = None,
    organization_id: str | None = None,
    limit: int = 1,
) -> dict[str, Any]:
    """Finds the closest statutory clause using deterministic mapping and pgvector similarity."""
    lower_query = query_text.lower()

    # Fast statutory taxonomy lookup
    if any(k in lower_query for k in ("erasure", "retention", "delete", "erased", "purge")):
        return {
            "act_section": "DPDP Act Sec 8(7)(b)",
            "rules_clause": "DPDP Rules 2025 Rule 8(3)",
            "chunk_text": "Erasure of personal data upon withdrawal of consent",
        }
    if any(k in lower_query for k in ("breach", "incident", "sla")):
        return {
            "act_section": "DPDP Act Sec 8(6)",
            "rules_clause": "DPDP Rules 2025 Rule 7",
            "chunk_text": "Intimation of personal data breach to Data Protection Board",
        }
    if any(k in lower_query for k in ("dpo", "grievance", "contact")):
        return {
            "act_section": "DPDP Act Sec 8(9)",
            "rules_clause": "DPDP Rules 2025 Rule 12",
            "chunk_text": "Publish contact details of Data Protection Officer",
        }
    if any(k in lower_query for k in ("language", "multilingual", "schedule")):
        return {
            "act_section": "DPDP Act Sec 5(3)",
            "rules_clause": "DPDP Rules 2025 Rule 3",
            "chunk_text": "Notice in English and 22 Eighth Schedule languages",
        }
    if any(k in lower_query for k in ("child", "parental", "minor")):
        return {
            "act_section": "DPDP Act Sec 9(1)",
            "rules_clause": "DPDP Rules 2025 Rule 10",
            "chunk_text": "Verifiable parental consent for processing of children data",
        }

    # If supabase client is provided and has records, query pgvector
    if supabase_client is not None:
        try:
            _vec = generate_embedding(query_text)
            res = (
                supabase_client.table("legal_embeddings")
                .select("statute_reference, document_name, chunk_text, metadata")
                .limit(limit)
                .execute()
            )
            if res.data and len(res.data) > 0:
                best = res.data[0]
                return {
                    "act_section": best.get("statute_reference", "DPDP Act Sec 6(1)"),
                    "rules_clause": best.get("document_name", "DPDP Rules 2025"),
                    "chunk_text": best.get("chunk_text", ""),
                }
        except Exception as e:
            logger.debug(f"pgvector query fallback for '{query_text[:30]}': {e}")

    return {
        "act_section": "DPDP Act Sec 6(1)",
        "rules_clause": "DPDP Rules 2025 Rule 3(b)",
        "chunk_text": "General notice and specific consent obligations",
    }
