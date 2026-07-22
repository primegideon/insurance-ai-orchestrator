import os
import logging
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
    # 1. Initialize Supabase Client
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # 2. Initialize IBM Embeddings (384 dimensions)
    embeddings = WatsonxEmbeddings(
        model_id="ibm/slate-30m-english-rtrvr-v2",
        url=os.environ.get("WATSONX_URL", ""),
        apikey=SecretStr(os.environ.get("WATSONX_API_KEY", "")),
        project_id=os.environ.get("WATSONX_PROJECT_ID", "")
    )
    
    # 3. Connect to the insurance_policies table
    return SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="insurance_policies",
        query_name="match_policies"
    )

def ingest_documents() -> str:
    """Loads, chunks, and uploads documents to Supabase pgvector."""
    DOCS_DIR.mkdir(exist_ok=True)
    documents = []
    
    for file_path in DOCS_DIR.glob("*"):
        if file_path.suffix == ".txt":
            documents.extend(TextLoader(str(file_path), encoding="utf-8").load())
        elif file_path.suffix == ".pdf":
            documents.extend(PyPDFLoader(str(file_path)).load())
            
    if not documents:
        return "No documents found in backend/documents/"
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    logger.info(f"Ingested {len(chunks)} chunks into Supabase.")
    return f"Success! {len(chunks)} chunks ingested into the cloud."

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