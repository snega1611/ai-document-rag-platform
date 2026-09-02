from pathlib import Path
import json

from ingestion.parser import parse_document, save_to_json
from ingestion.chunker import create_chunks
from ingestion.embedding import create_embeddings
from ingestion.vector_store import store_embeddings


# --------------------------------------------------
# Directories
# --------------------------------------------------

PARSED_DIR = Path("data/parsed")
CHUNKED_DIR = Path("data/chunked")
EMBEDDINGS_DIR = Path("data/embeddings")


# --------------------------------------------------
# Main ingestion pipeline
# --------------------------------------------------

def ingest_document(file_path, document_id):

    file_path = Path(file_path)

    # Make sure output directories exist
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKED_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("STARTING DOCUMENT INGESTION")
    print("=" * 60)

    # ==================================================
    # STEP 1: PARSE
    # ==================================================

    print("\n[1/4] Parsing document...")

    elements = parse_document(file_path)

    parsed_file = (
        PARSED_DIR
        / f"{file_path.stem}.json"
    )

    save_to_json(
        elements,
        parsed_file
    )

    print(f"Parsed JSON: {parsed_file}")

    # ==================================================
    # STEP 2: CHUNK
    # ==================================================

    print("\n[2/4] Creating chunks...")

    chunks = create_chunks(
        elements,
        max_tokens=250,
        overlap_tokens=30
    )

    chunked_file = (
        CHUNKED_DIR
        / f"{file_path.stem}.json"
    )

    with open(
        chunked_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            chunks,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Created {len(chunks)} chunks")
    print(f"Chunked JSON: {chunked_file}")

    # ==================================================
    # STEP 3: EMBEDDINGS
    # ==================================================

    print("\n[3/4] Creating embeddings...")

    embedded_chunks = create_embeddings(
        chunked_file
    )

    embeddings_file = (
        EMBEDDINGS_DIR
        / f"{file_path.stem}.json"
    )

    with open(
        embeddings_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            embedded_chunks,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Created embeddings for "
        f"{len(embedded_chunks)} chunks"
    )

    print(f"Embeddings JSON: {embeddings_file}")

    # ==================================================
    # STEP 4: VECTOR STORE
    # ==================================================

    print("\n[4/4] Storing vectors in ChromaDB...")

    stored_count = store_embeddings(
        embeddings_file,
        document_id
    )

    print(
        f"Stored {stored_count} vectors in ChromaDB"
    )

    # ==================================================
    # DONE
    # ==================================================

    print("\n" + "=" * 60)
    print("INGESTION COMPLETED")
    print("=" * 60)

    return {
        "file": file_path.name,
        "document_id": document_id,
        "pages": len(elements),
        "chunks": len(chunks),
        "embeddings": len(embedded_chunks),
        "stored": stored_count
    }


# --------------------------------------------------
# Manual testing
# --------------------------------------------------

# if __name__ == "__main__":

#     import sys

#     if len(sys.argv) < 2:

#         print(
#             "Usage: python ingest.py "
#             "<path_to_pdf_or_docx>"
#         )

#         sys.exit(1)

#     input_file = Path(sys.argv[1])

#     result = ingest_document(input_file)

#     print("\nResult:")
#     print(json.dumps(
#         result,
#         indent=2
#     ))
