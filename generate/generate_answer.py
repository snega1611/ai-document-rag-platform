import ollama


MODEL_NAME = "qwen3:1.7b"


def generate_answer(question, context):

    prompt = f"""
        You are a document question-answering assistant.

        Answer the QUESTION using ONLY the CONTEXT provided below.

        CONTEXT:
        {context}

        QUESTION:
        {question}

        Rules:
        - Give a direct, natural-language answer.
        - Answer in 1-3 complete sentences.
        - Do not answer with only a single word or phrase unless the question explicitly requires one.
        - Do not repeat the question.
        - Do not mention "context", "chunks", RAG, or the retrieval process.
        - Do not add information that is not supported by the context.
        - If the answer is explicitly present in the context, answer it directly.
        - If the answer is not present in the context, say:
        "I don't know based on the provided context."

        Return only the final answer.
        
        ANSWER:

        """

    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt
    )

    return response["response"].strip()