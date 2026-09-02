import time

from retrieval.retriever import retrieve, rerank, build_context
from generate.generate_answer import generate_answer

from prometheus_client import Histogram, Counter


RETRIEVE_TOP_K = 10
FINAL_TOP_K = 4


# --------------------------------
# Prometheus Metrics
# --------------------------------

# Time taken by ChromaDB retrieval
rag_retrieval_seconds = Histogram(
    "rag_retrieval_seconds",
    "Time taken to retrieve chunks from ChromaDB"
)


# Time taken by the LLM to generate an answer
rag_llm_seconds = Histogram(
    "rag_llm_seconds",
    "Time taken by the LLM to generate an answer"
)


# Number of LLM failures
rag_llm_failures_total = Counter(
    "rag_llm_failures_total",
    "Total number of LLM generation failures"
)


# --------------------------------
# RAG Pipeline
# --------------------------------

def rag_pipeline(question, document_ids):

    # --------------------------------
    # STEP 1: Retrieve chunks from ChromaDB
    # --------------------------------

    retrieval_start = time.time()

    chunks = retrieve(
        question,
        document_ids,
        RETRIEVE_TOP_K
    )

    retrieval_time = time.time() - retrieval_start

    rag_retrieval_seconds.observe(
        retrieval_time
    )

    print(
        f"\nChroma retrieval: "
        f"{retrieval_time:.2f}s"
    )

    print(f"Chroma retrieved: {len(chunks)} chunks")

    # Print retrieved results
    print("\n" + "=" * 60)
    print("CHROMA RESULTS")
    print("=" * 60)

    for i, chunk in enumerate(chunks, 1):

        print(f"\n--- Chunk {i} ---")
        print(f"Chroma Distance: {chunk['distance']:.4f}")
        print(f"Page: {chunk['metadata'].get('page')}")
        print(chunk["text"])


    # --------------------------------
    # STEP 2: Rerank chunks using CrossEncoder
    # --------------------------------

    chunks = rerank(
        question,
        chunks,
        FINAL_TOP_K
    )

    print("\n" + "=" * 60)
    print("RERANKED RESULTS")
    print("=" * 60)

    for i, chunk in enumerate(chunks, 1):

        print(f"\n--- Chunk {i} ---")
        print(f"Rerank Score: {chunk['rerank_score']:.4f}")
        print(f"Chroma Distance: {chunk['distance']:.4f}")
        print(f"Page: {chunk['metadata'].get('page')}")
        print(chunk["text"])


    # --------------------------------
    # STEP 3: Build context
    # --------------------------------

    context = build_context(chunks)

    print("\n" + "=" * 60)
    print("CONTEXT FOR LLM")
    print("=" * 60)

    print(context)


    # --------------------------------
    # STEP 4: Generate answer using LLM
    # --------------------------------

    llm_start = time.time()

    try:

        answer = generate_answer(
            question,
            context
        )

    except Exception:

        rag_llm_failures_total.inc()

        print(
            "\nLLM GENERATION FAILED"
        )

        raise

    finally:

        llm_time = time.time() - llm_start

        rag_llm_seconds.observe(
            llm_time
        )

        print(
            f"\nLLM latency: "
            f"{llm_time:.2f}s"
        )


    return {
        "answer": answer,
        "context": context
    }

# --------------------------------
# Main
# --------------------------------

# if __name__ == "__main__":

#     question = input("\nAsk a question: ")

#     answer = rag_pipeline(question)

#     print("\n" + "=" * 60)
#     print("FINAL ANSWER")
#     print("=" * 60)

#     print(answer)