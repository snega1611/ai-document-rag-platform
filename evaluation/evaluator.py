from ragas import evaluate
from ragas.metrics import Faithfulness
from ragas.llms import LangchainLLMWrapper

from langchain_ollama import ChatOllama

from datasets import Dataset

from database import save_evaluation


# --------------------------------------------------
# Ragas evaluator LLM
# --------------------------------------------------

llm = ChatOllama(
    model="qwen3:1.7b",
    temperature=0
)

evaluator_llm = LangchainLLMWrapper(
    llm
)


# --------------------------------------------------
# Metric
# --------------------------------------------------

faithfulness = Faithfulness(
    llm=evaluator_llm
)


# --------------------------------------------------
# Evaluate one response
# --------------------------------------------------

def evaluate_response(
    question,
    context,
    answer
):

    # --------------------------------------------------
    # Start evaluation
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("STARTING RAGAS EVALUATION")
    print("=" * 60)


    # --------------------------------------------------
    # Create evaluation dataset
    # --------------------------------------------------

    dataset = Dataset.from_dict({

        "user_input": [
            question
        ],

        "retrieved_contexts": [
            [context]
        ],

        "response": [
            answer
        ],

    })


    # --------------------------------------------------
    # Run Ragas
    # --------------------------------------------------

    result = evaluate(
        dataset=dataset,

        metrics=[
            faithfulness
        ],

        llm=evaluator_llm
    )


    # --------------------------------------------------
    # Extract score
    # --------------------------------------------------

    scores = result.to_pandas().iloc[0]

    faithfulness_score = float(
        scores["faithfulness"]
    )


    # --------------------------------------------------
    # Save result to PostgreSQL
    # --------------------------------------------------

    save_evaluation(

        question=question,

        answer=answer,

        faithfulness_score=faithfulness_score

    )


    # --------------------------------------------------
    # Evaluation complete
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("RAGAS EVALUATION COMPLETE")
    print("=" * 60)

    print(
        f"Faithfulness: {faithfulness_score:.4f}"
    )

    print(
        "Saved evaluation to PostgreSQL"
    )


    # --------------------------------------------------
    # Return Ragas result
    # --------------------------------------------------

    return result

