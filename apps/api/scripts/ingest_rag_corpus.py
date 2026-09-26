import logging
import re
from pathlib import Path
from typing import Any

from apps.api.config import get_settings
from apps.api.tools.embeddings import generate_embedding
from supabase import Client, create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_rag_corpus")


def parse_dpdp_act_chunks(content: str) -> list[dict[str, Any]]:
    """Semantically parses DPDP Act 2023 markdown into statutory section chunks."""
    chunks: list[dict[str, Any]] = []

    # Find Chapters and Sections
    chapters = re.split(r"(## CHAPTER [I|V|X]+:? [^\n]+)", content)
    current_chapter = "PRELIMINARY"

    for part in chapters:
        if part.startswith("## CHAPTER"):
            current_chapter = part.replace("##", "").strip()
            continue

        # Split into sections: ### <num>. <title>
        sections = re.split(r"(### \d+\. [^\n]+)", part)
        for i in range(1, len(sections), 2):
            sec_header = sections[i].strip()
            sec_body = sections[i + 1].strip() if i + 1 < len(sections) else ""

            # Extract section number
            sec_match = re.search(r"### (\d+)\.\s*(.*)", sec_header)
            if sec_match:
                sec_num = sec_match.group(1)
                sec_title = sec_match.group(2).strip()
                statute_ref = f"DPDP Act Sec {sec_num}"

                full_chunk_text = (
                    f"DPDP Act 2023 | {current_chapter} | Section {sec_num}: {sec_title}\n\n"
                    f"{sec_body}"
                )

                chunks.append(
                    {
                        "document_name": "DPDP Act 2023",
                        "statute_reference": statute_ref,
                        "chunk_text": full_chunk_text,
                        "metadata": {
                            "chapter": current_chapter,
                            "section_number": int(sec_num),
                            "section_title": sec_title,
                        },
                    }
                )

    # Check for Schedule
    if "## THE SCHEDULE" in content:
        schedule_part = content.split("## THE SCHEDULE", 1)[1]
        chunks.append(
            {
                "document_name": "DPDP Act 2023",
                "statute_reference": "DPDP Act Schedule",
                "chunk_text": f"DPDP Act 2023 | SCHEDULE OF PENALTIES\n\n{schedule_part.strip()}",
                "metadata": {"chapter": "SCHEDULE", "section_title": "Penalties for Breach"},
            }
        )

    return chunks


def parse_dpdp_rules_chunks(content: str) -> list[dict[str, Any]]:
    """Semantically parses DPDP Rules 2025 markdown into rule chunks."""
    chunks: list[dict[str, Any]] = []

    rules = re.split(r"(### \d+\. [^\n]+)", content)
    for i in range(1, len(rules), 2):
        rule_header = rules[i].strip()
        rule_body = rules[i + 1].strip() if i + 1 < len(rules) else ""

        rule_match = re.search(r"### (\d+)\.\s*(.*)", rule_header)
        if rule_match:
            rule_num = rule_match.group(1)
            rule_title = rule_match.group(2).strip()
            statute_ref = f"DPDP Rules 2025 Rule {rule_num}"

            full_chunk_text = (
                f"DPDP Rules 2025 | Rule {rule_num}: {rule_title}\n\n"
                f"{rule_body}"
            )

            chunks.append(
                {
                    "document_name": "DPDP Rules 2025",
                    "statute_reference": statute_ref,
                    "chunk_text": full_chunk_text,
                    "metadata": {
                        "rule_number": int(rule_num),
                        "rule_title": rule_title,
                    },
                }
            )

    # First Schedule and Second Schedule
    if "### FIRST SCHEDULE" in content or "PART A" in content:
        schedules = re.split(r"(## [A-Z ]+SCHEDULE|### [A-Z ]+SCHEDULE)", content)
        for j in range(1, len(schedules), 2):
            sched_header = schedules[j].strip()
            sched_body = schedules[j + 1].strip() if j + 1 < len(schedules) else ""
            chunks.append(
                {
                    "document_name": "DPDP Rules 2025",
                    "statute_reference": f"DPDP Rules 2025 {sched_header.replace('#', '').strip()}",
                    "chunk_text": f"DPDP Rules 2025 | {sched_header}\n\n{sched_body.strip()}",
                    "metadata": {"schedule": sched_header},
                }
            )

    return chunks


def parse_summary_chunks(content: str) -> list[dict[str, Any]]:
    """Parses executive summary document into topic chunks."""
    chunks: list[dict[str, Any]] = []
    sections = re.split(r"(### [^\n]+)", content)

    for i in range(1, len(sections), 2):
        sec_header = sections[i].strip()
        sec_body = sections[i + 1].strip() if i + 1 < len(sections) else ""

        title = sec_header.replace("###", "").strip()
        if not title:
            continue

        statute_ref = f"EY DPDP Framework | {title}"

        chunks.append(
            {
                "document_name": "EY DPDP Summary",
                "statute_reference": statute_ref,
                "chunk_text": f"EY DPDP Compliance Framework | {title}\n\n{sec_body.strip()}",
                "metadata": {"topic": title},
            }
        )

    return chunks


def load_and_chunk_rag_corpus(rag_dir: Path) -> list[dict[str, Any]]:
    """Loads all markdown files in context/RAG and produces semantic chunks."""
    all_chunks: list[dict[str, Any]] = []

    act_file = rag_dir / "digital_personal_data_protection_act_2023 (1).md"
    if act_file.exists():
        logger.info(f"Chunking {act_file.name}...")
        act_content = act_file.read_text(encoding="utf-8")
        act_chunks = parse_dpdp_act_chunks(act_content)
        all_chunks.extend(act_chunks)
        logger.info(f"Generated {len(act_chunks)} chunks for DPDP Act 2023.")

    rules_file = rag_dir / "digital_personal_data_protection_rules_2025.md"
    if rules_file.exists():
        logger.info(f"Chunking {rules_file.name}...")
        rules_content = rules_file.read_text(encoding="utf-8")
        rules_chunks = parse_dpdp_rules_chunks(rules_content)
        all_chunks.extend(rules_chunks)
        logger.info(f"Generated {len(rules_chunks)} chunks for DPDP Rules 2025.")

    summary_file = rag_dir / "ey_india_dpdp_act_2023_summary.md"
    if summary_file.exists():
        logger.info(f"Chunking {summary_file.name}...")
        summary_content = summary_file.read_text(encoding="utf-8")
        summary_chunks = parse_summary_chunks(summary_content)
        all_chunks.extend(summary_chunks)
        logger.info(f"Generated {len(summary_chunks)} chunks for EY Summary.")

    return all_chunks


def ingest_corpus_into_supabase(
    chunks: list[dict[str, Any]], supabase_client: Client | None = None
) -> int:
    """Embeds each chunk and upserts into legal_embeddings table."""
    settings = get_settings()
    client = supabase_client or create_client(
        settings.NEXT_PUBLIC_SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY or settings.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    )

    logger.info(f"Ingesting {len(chunks)} statutory chunks into legal_embeddings...")
    success_count = 0

    for idx, chunk in enumerate(chunks):
        embedding_vec = generate_embedding(chunk["chunk_text"])

        payload = {
            "organization_id": None,
            "audit_id": None,
            "document_name": chunk["document_name"],
            "statute_reference": chunk["statute_reference"],
            "chunk_text": chunk["chunk_text"],
            "embedding": embedding_vec,
            "metadata": chunk.get("metadata", {}),
        }

        try:
            res = client.table("legal_embeddings").insert(payload).execute()
            if res.data:
                success_count += 1
            if (idx + 1) % 10 == 0 or idx == len(chunks) - 1:
                logger.info(f"Progress: {idx + 1}/{len(chunks)} chunks embedded and inserted.")
        except Exception as e:
            logger.error(f"Failed to insert chunk {chunk['statute_reference']}: {e}")

    logger.info(f"Ingestion complete: {success_count}/{len(chunks)} chunks inserted.")
    return success_count


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[3]
    rag_dir = base_dir / "context" / "RAG"

    if not rag_dir.exists():
        rag_dir = Path("context/RAG").resolve()

    logger.info(f"Loading RAG corpus from {rag_dir}...")
    corpus_chunks = load_and_chunk_rag_corpus(rag_dir)
    ingest_corpus_into_supabase(corpus_chunks)
