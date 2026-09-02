import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder


# --------------------------------
# Configuration
# --------------------------------

CHROMA_PATH = "data/vectorstore"
COLLECTION_NAME = "documents"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# --------------------------------
# Load models
# --------------------------------

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

reranker = CrossEncoder(
    RERANKER_MODEL
)


# --------------------------------
# Connect to Chroma
# --------------------------------

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

def get_collection():

    return client.get_collection(
        name=COLLECTION_NAME
    )


# --------------------------------
# STEP 1: Retrieve
# --------------------------------

def retrieve(question, document_ids, top_K):
    
    print("\n" + "=" * 60)
    print("DOCUMENTS BEING SEARCHED")
    print("=" * 60)
    
    for document_id in document_ids:
        print(document_id)

    collection = get_collection()


    # Convert question into vector
    question_vector = embedding_model.encode(
        question
    ).tolist()


    # Search ChromaDB
    results = collection.query(

        query_embeddings=[
            question_vector
        ],

        n_results=top_K,

        # Search only user's documents
        where={
            "document_id": {
                "$in": document_ids
            }
        }
    )


    chunks = []


    for text, metadata, distance in zip(

        results["documents"][0],

        results["metadatas"][0],

        results["distances"][0]

    ):

        chunks.append({

            "text": text,

            "metadata": metadata,

            "distance": distance

        })
        
        print(
            f"Retrieved document: "
            f"{metadata.get('document_id')}"
        )


    return chunks


# --------------------------------
# STEP 2: Rerank
# --------------------------------


def rerank(question, chunks, final_top_K):

    pairs = [
        [question, chunk["text"]]
        for chunk in chunks
    ]

    scores = reranker.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    chunks.sort(
        key=lambda chunk: chunk["rerank_score"],
        reverse=True
    )

    # PRINT ALL RERANKER RESULTS
    print("\n" + "=" * 60)
    print("ALL RERANKER SCORES")
    print("=" * 60)

    for i, chunk in enumerate(chunks, 1):

        print(
            f"{i}. "
            f"Score: {chunk['rerank_score']:.4f} | "
            f"Chroma Distance: {chunk['distance']:.4f} | "
            f"Page: {chunk['metadata'].get('page')}"
        )

    return chunks[:final_top_K]


# --------------------------------
# STEP 3: Build context
# --------------------------------

def build_context(chunks):

    context = ""

    for i, chunk in enumerate(chunks, 1):

        page = chunk["metadata"].get("page")

        context += (
            f"[{i}] Page: {page}\n"
            f"{chunk['text']}\n\n"
        )

    return context

def debug_documents():

    collection = get_collection()

    result = collection.get(
        include=["metadatas"]
    )

    print("\n" + "=" * 60)
    print("DOCUMENT IDs STORED IN CHROMA")
    print("=" * 60)

    document_ids = set()

    for metadata in result["metadatas"]:

        document_id = metadata.get("document_id")

        if document_id:
            document_ids.add(document_id)

    for document_id in document_ids:
        print(document_id)

    print(
        f"\nTotal documents in Chroma: "
        f"{len(document_ids)}"
    )
    
if __name__ == "__main__":
    debug_documents()
# --------------------------------
# Main
# --------------------------------

# if __name__ == "__main__":

#     question = input("Ask a question: ")

#     # --------------------------------
#     # Chroma retrieval
#     # --------------------------------

#     chunks = retrieve(question, 10)

#     print(f"\nChroma retrieved: {len(chunks)} chunks")

#     print("\n" + "=" * 60)
#     print("CHROMA RESULTS")
#     print("=" * 60)

#     for i, chunk in enumerate(chunks, 1):

#         print(f"\n--- Chunk {i} ---")

#         print(
#             f"Chroma Distance: "
#             f"{chunk['distance']:.4f}"
#         )

#         print(
#             f"Page: "
#             f"{chunk['metadata'].get('page')}"
#         )

#         print(chunk["text"])


#     # --------------------------------
#     # CrossEncoder reranking
#     # --------------------------------

#     chunks = rerank(
#         question,
#         chunks,
#         3
#     )

#     print(f"\nAfter reranking: {len(chunks)} chunks")

#     print("\n" + "=" * 60)
#     print("RERANKED RESULTS")
#     print("=" * 60)

#     for i, chunk in enumerate(chunks, 1):

#         print(f"\n--- Chunk {i} ---")

#         print(
#             f"Rerank Score: "
#             f"{chunk['rerank_score']:.4f}"
#         )

#         print(
#             f"Chroma Distance: "
#             f"{chunk['distance']:.4f}"
#         )

#         print(
#             f"Page: "
#             f"{chunk['metadata'].get('page')}"
#         )

#         print(chunk["text"])


#     # --------------------------------
#     # Build context for LLM
#     # --------------------------------

#     context = build_context(chunks)

#     print("\n" + "=" * 60)
#     print("CONTEXT FOR LLM")
#     print("=" * 60)

#     print(context)
