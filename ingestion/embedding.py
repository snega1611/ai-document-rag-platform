from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
import sys

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(input_file):
    # Read chunks
    with open(input_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Get text from each chunk
    texts = [chunk["text"] for chunk in chunks]

    # Create embeddings
    embeddings = model.encode(texts)

    # Add embedding to each chunk
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    return chunks


# if __name__ == "__main__":

#     if len(sys.argv) < 2:
#         print("Usage: python embedding.py data/chunked/<filename>.json")
#         sys.exit(1)

#     input_file = Path(sys.argv[1])

#     embedded_chunks = create_embeddings(input_file)

#     # Save embeddings
#     output_dir = Path("data/embeddings")
#     output_dir.mkdir(parents=True, exist_ok=True)

#     output_file = output_dir / input_file.name

#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(
#             embedded_chunks,
#             f,
#             indent=2,
#             ensure_ascii=False
#         )

#     print(f"Done! Created embeddings for {len(embedded_chunks)} chunks")
#     print(f"Saved to: {output_file}")