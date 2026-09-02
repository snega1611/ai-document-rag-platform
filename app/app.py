import time
import uuid

from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import shutil
from pydantic import BaseModel

from rag_pipeline import rag_pipeline
from ingestion.ingest import ingest_document

from evaluation.queue import evaluation_queue
from evaluation.evaluator import evaluate_response

from cache.redis_cache import (
    get_cached_answer,
    cache_answer,
    save_user_document,
    get_user_documents,
    save_chat_message,
    get_chat_history
)

from database import (
    save_document,
    save_question,
    create_documents_table,
    create_questions_table,
    create_evaluations_table,
)

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Histogram, Counter


app = FastAPI()


# ============================================================
# PROMETHEUS
# ============================================================

Instrumentator().instrument(app).expose(app)


# ------------------------------------------------------------
# 1. DOCUMENT INGESTION LATENCY
# ------------------------------------------------------------

document_ingestion_seconds = Histogram(
    "document_ingestion_seconds",
    "Time taken to ingest a document"
)


# ------------------------------------------------------------
# 2. CACHE LATENCY
#
# operation:
#   read  -> Redis cache lookup
#   write -> Redis cache write
# ------------------------------------------------------------

cache_latency_seconds = Histogram(
    "cache_latency_seconds",
    "Time taken for Redis cache operations",
    ["operation"]
)


# ------------------------------------------------------------
# 3. RAG LATENCY
# ------------------------------------------------------------

rag_latency_seconds = Histogram(
    "rag_latency_seconds",
    "Time taken by the RAG pipeline"
)


# ------------------------------------------------------------
# 4. RAG FAILURES
# ------------------------------------------------------------

rag_failures_total = Counter(
    "rag_failures_total",
    "Total number of RAG pipeline failures"
)


# ------------------------------------------------------------
# 5. TOTAL RAG REQUESTS
# ------------------------------------------------------------

rag_requests_total = Counter(
    "rag_requests_total",
    "Total number of /ask requests"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

create_documents_table()
create_questions_table()
create_evaluations_table()


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    question: str
    session_id: str


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

@app.post("/upload")
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
):

    # -----------------------------------------------
    # 1. Generate unique document ID
    # -----------------------------------------------

    document_id = str(uuid.uuid4())

    print("\n" + "=" * 60)
    print("NEW DOCUMENT UPLOAD")
    print("=" * 60)

    print("Session ID:", session_id)
    print("Document ID:", document_id)
    print("Filename:", file.filename)


    # -----------------------------------------------
    # 2. Save file
    # -----------------------------------------------

    file_path = UPLOAD_DIR / file.filename

    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )


    # -----------------------------------------------
    # 3. Ingest document
    # -----------------------------------------------

    ingestion_start = time.time()

    result = ingest_document(
        file_path,
        document_id
    )

    ingestion_time = time.time() - ingestion_start

    document_ingestion_seconds.observe(
        ingestion_time
    )

    print(
        f"\nDocument ingestion: "
        f"{ingestion_time:.2f}s"
    )

    print("\n" + "=" * 60)
    print("INGESTION RESULT")
    print("=" * 60)

    print(result)


    # -----------------------------------------------
    # 4. Save document to PostgreSQL
    # -----------------------------------------------

    save_document(
        document_id=document_id,
        session_id=session_id,
        filename=file.filename,
        status="completed"
    )


    # -----------------------------------------------
    # 5. Remember document for this session
    # -----------------------------------------------

    save_user_document(
        session_id,
        document_id
    )

    print(
        "Saved document to Redis:",
        document_id
    )

    print(
        "Current user documents:",
        get_user_documents(session_id)
    )


    # -----------------------------------------------
    # 6. Return
    # -----------------------------------------------

    return {
        "message": "Document uploaded and ingested successfully",
    }


# ============================================================
# DOCUMENTS
# ============================================================

@app.get("/documents/{session_id}")
def get_documents(session_id: str):

    documents = get_user_documents(
        session_id
    )

    return {
        "session_id": session_id,
        "documents": documents,
        "count": len(documents)
    }


# ============================================================
# ASK QUESTION
# ============================================================

@app.post("/ask")
def ask_question(request: ChatRequest):

    # -----------------------------------------------
    # TOTAL RAG REQUEST COUNT
    # -----------------------------------------------

    rag_requests_total.inc()

    start = time.time()


    # -----------------------------------------------
    # 1. Get user's documents from Redis
    # -----------------------------------------------

    document_ids = get_user_documents(
        request.session_id
    )

    print(
        f"User documents: {document_ids}"
    )


    # -----------------------------------------------
    # No documents found
    # -----------------------------------------------

    if not document_ids:

        return {
            "answer": (
                "I don't have any documents available "
                "for this session. Please upload a document first."
            )
        }


    print(
        f"Found {len(document_ids)} document(s)"
    )


    # -----------------------------------------------
    # 2. Check Redis cache
    # -----------------------------------------------

    cache_start = time.time()

    for document_id in document_ids:

        cached = get_cached_answer(
            document_id,
            request.question
        )

        if cached:

            cache_read_time = (
                time.time() - cache_start
            )

            cache_latency_seconds.labels(
                operation="read"
            ).observe(
                cache_read_time
            )

            print(
                f"REDIS CACHE HIT: {document_id}"
            )

            print(
                f"Redis read: "
                f"{cache_read_time:.2f}s"
            )

            return {
                "answer": cached["answer"]
            }


    cache_read_time = (
        time.time() - cache_start
    )

    cache_latency_seconds.labels(
        operation="read"
    ).observe(
        cache_read_time
    )

    print("REDIS CACHE MISS")

    print(
        f"Redis read: "
        f"{cache_read_time:.2f}s"
    )


    # -----------------------------------------------
    # Save question to PostgreSQL
    # -----------------------------------------------

    save_question(
        session_id=request.session_id,
        document_id=None,
        question=request.question
    )


    # -----------------------------------------------
    # 3. Run RAG
    # -----------------------------------------------

    rag_start = time.time()

    try:

        result = rag_pipeline(
            request.question,
            document_ids
        )

    except Exception:

        rag_failures_total.inc()

        print(
            "\nRAG PIPELINE FAILED"
        )

        raise

    finally:

        rag_time = time.time() - rag_start

        rag_latency_seconds.observe(
            rag_time
        )

        print(
            f"RAG total: "
            f"{rag_time:.2f}s"
        )


    answer = result["answer"]

    context = result["context"]


    # -----------------------------------------------
    # 4. Save chat history
    # -----------------------------------------------

    save_chat_message(
        request.session_id,
        "user",
        request.question
    )

    save_chat_message(
        request.session_id,
        "assistant",
        answer
    )


    # -----------------------------------------------
    # 5. Cache answer
    # -----------------------------------------------

    cache_start = time.time()

    for document_id in document_ids:

        cache_answer(
            document_id,
            request.question,
            answer
        )


    cache_write_time = (
        time.time() - cache_start
    )

    cache_latency_seconds.labels(
        operation="write"
    ).observe(
        cache_write_time
    )

    print(
        f"Cache write: "
        f"{cache_write_time:.2f}s"
    )


    # -----------------------------------------------
    # 6. Queue Ragas
    # -----------------------------------------------

    queue_start = time.time()

    job = evaluation_queue.enqueue(
        evaluate_response,
        request.question,
        context,
        answer,
        job_timeout=600
    )

    queue_time = (
        time.time() - queue_start
    )

    print(
        f"Ragas enqueue: "
        f"{queue_time:.2f}s"
    )

    print(
        "Ragas job:",
        job.id
    )


    # -----------------------------------------------
    # 7. TOTAL /ask
    # -----------------------------------------------

    print(
        f"TOTAL /ask: "
        f"{time.time() - start:.2f}s"
    )


    return {
        "answer": answer
    }


# ============================================================
# CHAT HISTORY
# ============================================================

@app.get("/chat-history")
def chat_history(session_id: str):

    return {
        "messages": get_chat_history(session_id)
    }