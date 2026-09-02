import json
import sys
from pathlib import Path
import tiktoken

# Load OpenAI's default tokenizer (cl100k_base is used for gpt-4, gpt-3.5-turbo, and text-embedding-3)
encoder = tiktoken.get_encoding("cl100k_base")

def get_token_count(text):
    return len(encoder.encode(text))

'''
Reads each element one by one.
Gets the text from that element.
Adds the text to the current chunk.
Uses tiktoken to count tokens.
Checks: Is the chunk bigger than 250 tokens?
No → keep adding more text.
Yes → save the current chunk.
Before starting the next chunk, it takes the last 30 tokens from the previous chunk.
Adds those 30 tokens to the beginning of the next chunk → this is overlap.
Continues until the entire document is processed.
Saves the final leftover text as the last chunk.
Returns all the chunks.
'''

def create_chunks(elements, max_tokens=250, overlap_tokens=30):
    chunks = []
    current_text = ""
    current_page = None
    chunk_id = 0

    for elem in elements:

        # ----------------
        # Get page
        # ----------------

        if elem.get("page") is not None:
            current_page = elem.get("page")

        # =====================================================
        # TABLE
        # =====================================================

        if elem.get("type") == "table" and elem.get("data"):

            # First save any normal text that is currently
            # waiting to become a chunk
            if current_text:

                chunks.append({
                    "chunk_id": chunk_id,
                    "text": current_text,
                    "page": current_page,
                    "file_name": elem.get("file_name"),
                    "token_count": get_token_count(current_text)
                })

                chunk_id += 1
                current_text = ""

            # ----------------
            # Each table row = one chunk
            # ----------------

            for row in elem["data"]:

                row_text = []

                for key, value in row.items():

                    if value is not None and str(value).strip():

                        row_text.append(
                            f"{key}: {value}"
                        )

                if not row_text:
                    continue

                table_text = " | ".join(row_text)

                chunks.append({
                    "chunk_id": chunk_id,
                    "text": table_text,
                    "page": current_page,
                    "file_name": elem.get("file_name"),
                    "token_count": get_token_count(table_text)
                })

                chunk_id += 1

            # Move to next element
            continue

        # =====================================================
        # NORMAL TEXT
        # =====================================================

        text = elem.get("text", "").strip()

        if not text:
            continue

        candidate_text = (
            (current_text + "\n\n" + text).strip()
            if current_text
            else text
        )

        # ----------------
        # Check token count
        # ----------------

        if get_token_count(candidate_text) > max_tokens and current_text:

            chunks.append({
                "chunk_id": chunk_id,
                "text": current_text,
                "page": current_page,
                "file_name": elem.get("file_name"),
                "token_count": get_token_count(current_text)
            })

            chunk_id += 1

            # ----------------
            # TOKEN OVERLAP
            # ----------------

            tokens = encoder.encode(current_text)

            overlap_token_ids = (
                tokens[-overlap_tokens:]
                if len(tokens) > overlap_tokens
                else tokens
            )

            overlap_text = encoder.decode(
                overlap_token_ids
            )

            current_text = (
                overlap_text + "\n\n" + text
            ).strip()

        else:

            current_text = candidate_text

    # =====================================================
    # SAVE LEFTOVER NORMAL TEXT
    # =====================================================

    if current_text:

        chunks.append({
            "chunk_id": chunk_id,
            "text": current_text,
            "page": current_page,
            "file_name": elem.get("file_name"),
            "token_count": get_token_count(current_text)
        })

    return chunks

#get input file, open the parsed json and load as python data, get teh chunks, create a output file and write the chunks to it

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python chunker.py data/parsed/<filename>.json")
#         sys.exit(1)

#     input_file = Path(sys.argv[1])
    
#     with open(input_file, "r", encoding="utf-8") as f:
#         elements = json.load(f)

#     # Max 250 tokens per chunk, 30 tokens overlap
#     chunks = create_chunks(elements, max_tokens=250, overlap_tokens=30)

#     output_dir = Path("data/chunked")
#     output_dir.mkdir(parents=True, exist_ok=True)
#     output_file = output_dir / input_file.name

#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(chunks, f, indent=2, ensure_ascii=False)

#     print(f"Done! Created {len(chunks)} token-based chunks saved to {output_file}")
    
