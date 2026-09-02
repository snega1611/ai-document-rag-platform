import chromadb
import json
import sys
from pathlib import Path


# Create local ChromaDB
chroma_client = chromadb.PersistentClient(
    path="data/vectorstore"
)

# Create collection
document_collection = chroma_client.get_or_create_collection(
    name="documents"
)


def store_embeddings(input_file, document_id):

    # Read embedded chunks
    with open(input_file, "r", encoding="utf-8") as f:
        embedded_chunks = json.load(f)

    # Store each embedded chunk
    for chunk in embedded_chunks:

        document_collection.add(
            ids=[
                f"{chunk['file_name']}_{chunk['chunk_id']}"
            ],

            documents=[
                chunk["text"]
            ],

            embeddings=[
                chunk["embedding"]
            ],

            metadatas=[{
                "file_name": str(chunk["file_name"]),
                "document_id": document_id,
                "page": str(chunk["page"]),
                "token_count": chunk["token_count"],
            }]
        )

    return len(embedded_chunks)


# if __name__ == "__main__":

#     if len(sys.argv) < 2:
#         print(
#             "Usage: python vector_store.py "
#             "data/embeddings/<filename>.json"
#         )
#         sys.exit(1)

#     input_file = Path(sys.argv[1])

#     stored_count = store_embeddings(input_file)

#     print(
#         f"Done! Stored {stored_count} vectors in ChromaDB"
#     )

