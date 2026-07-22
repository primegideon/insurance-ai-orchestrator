import os
import logging
import traceback
from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import create_client, Client
from langchain_ibm import WatsonxEmbeddings
from pydantic import SecretStr

logger = logging.getLogger(__name__)

# Directory for your sample documents
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "documents"


def get_vector_store() -> SupabaseVectorStore:
    """Connects to the Supabase pgvector database."""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    supabase: Client = create_client(supabase_url, supabase_key)

    embeddings = WatsonxEmbeddings(
        model_id="ibm/slate-30m-english-rtrvr-v2",
        url=os.environ.get("WATSONX_URL", ""),
        apikey=SecretStr(os.environ.get("WATSONX_API_KEY", "")),
        project_id=os.environ.get("WATSONX_PROJECT_ID", "")
    )

    return SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="insurance_policies",
        query_name="match_policies"
    )


def ingest_documents() -> dict:
    """Loads, chunks, and uploads documents to Supabase pgvector.

    Returns a progress dict so every step is visible in the API response.
    If a step fails its value will be an ERROR string with the full traceback.
    """
    steps: dict = {}

    # ── Step 1: locate documents ──────────────────────────────────────────
    try:
        DOCS_DIR.mkdir(exist_ok=True)
        found = [p for p in DOCS_DIR.glob("*") if p.suffix in (".txt", ".pdf")]
        steps["step1_find_files"] = [p.name for p in found]
        logger.info("Ingest step 1 — found: %s", steps["step1_find_files"])
    except Exception:
        steps["step1_find_files"] = f"ERROR: {traceback.format_exc()}"
        return steps

    if not found:
        steps["result"] = "No documents found in backend/app/documents/"
        return steps

    # ── Step 2: load documents ────────────────────────────────────────────
    try:
        documents = []
        for file_path in found:
            if file_path.suffix == ".txt":
                documents.extend(TextLoader(str(file_path), encoding="utf-8").load())
            elif file_path.suffix == ".pdf":
                documents.extend(PyPDFLoader(str(file_path)).load())
        steps["step2_load_docs"] = f"{len(documents)} document(s) loaded"
        logger.info("Ingest step 2 — %s", steps["step2_load_docs"])
    except Exception:
        steps["step2_load_docs"] = f"ERROR: {traceback.format_exc()}"
        return steps

    # ── Step 3: chunk ─────────────────────────────────────────────────────
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(documents)
        steps["step3_chunk"] = f"{len(chunks)} chunks created"
        logger.info("Ingest step 3 — %s", steps["step3_chunk"])
    except Exception:
        steps["step3_chunk"] = f"ERROR: {traceback.format_exc()}"
        return steps

    # ── Step 4: embed + upsert to pgvector ───────────────────────────────
    try:
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
        steps["step4_upsert"] = f"OK — {len(chunks)} chunks upserted"
        logger.info("Ingest step 4 — %s", steps["step4_upsert"])
    except Exception:
        steps["step4_upsert"] = f"ERROR: {traceback.format_exc()}"
        return steps

    steps["result"] = f"Success! {len(chunks)} chunks ingested into the cloud."
    return steps


def retrieve_policy_clauses(query: str, k: int = 2) -> str:
    """Retrieves the most relevant policy rules from the database."""
    try:
        vector_store = get_vector_store()
        results = vector_store.similarity_search(query, k=k)
        if not results:
            return "No specific policy clauses found in documentation."
        return "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return "Error retrieving clauses."