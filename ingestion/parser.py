from pathlib import Path
import json
import sys

from docling.document_converter import DocumentConverter


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx"
}

converter = DocumentConverter()


def parse_document(file_path):

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {file_path.suffix}. "
            f"Supported types: PDF and DOCX."
        )

    print(f"Parsing: {file_path.name}")

    result = converter.convert(str(file_path))

    doc = result.document

    print(f"Text elements: {len(doc.texts)}")
    print(f"Tables: {len(doc.tables)}")
    print(f"Pictures: {len(doc.pictures)}")

    elements = []

    # -----------------------------
    # Extract text
    # -----------------------------

    for item in doc.texts:

        text = getattr(item, "text", None)

        if not text:
            continue
        
        print(
        "TYPE:",
        item.label.value,
        "| TEXT:",
        repr(text[:150])
        )

        item_type = item.label.value

        page_number = None

        if item.prov:
            page_number = item.prov[0].page_no

        elements.append({
            "text": text.strip(),
            "type": item_type,
            "page": page_number,
            "file_name": file_path.name
        })

    # -----------------------------
    # Extract tables
    # -----------------------------

    for table in doc.tables:

        page_number = None

        if table.prov:
            page_number = table.prov[0].page_no

        try:

            dataframe = table.export_to_dataframe(doc=doc)

            table_data = dataframe.fillna("").to_dict(
                orient="records"
            )

        except Exception as e:

            print(f"Could not extract table: {e}")

            table_data = []

        elements.append({
            "text": "",
            "type": "table",
            "page": page_number,
            "data": table_data,
            "file_name": file_path.name
        })

    # -----------------------------
    # Sort by page
    # -----------------------------

    elements.sort(
        key=lambda x: (
            x["page"]
            if x["page"] is not None
            else 999999
        )
    )

    print(f"Extracted elements: {len(elements)}")

    return elements


def save_to_json(elements, output_file):

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            elements,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved: {output_file}")


def load_from_json(json_file):

    with open(
        json_file,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# if __name__ == "__main__":

#     # Make sure a file was provided
#     if len(sys.argv) < 2:
#         print(
#             "Usage: python ingestion/parser.py <file_path>"
#         )
#         sys.exit(1)

#     # Get input file from command line
#     input_file = Path(sys.argv[1])

#     # Automatically create JSON filename
#     output_file = (
#         Path("data/parsed")
#         / f"{input_file.stem}.json"
#     )

#     # Parse document
#     elements = parse_document(input_file)

#     # Save parsed result
#     save_to_json(
#         elements,
#         output_file
#     )