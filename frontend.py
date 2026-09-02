import streamlit as st
import requests
import uuid


# --------------------------------------------------
# Configuration
# --------------------------------------------------

import os

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://127.0.0.1:8000"
)


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="📄",
    layout="centered"
)


# --------------------------------------------------
# Persistent session ID
# --------------------------------------------------

if "session_id" not in st.session_state:

    params = st.query_params

    if "session_id" in params:

        st.session_state.session_id = params["session_id"]

    else:

        new_session_id = str(uuid.uuid4())

        st.query_params["session_id"] = new_session_id

        st.session_state.session_id = new_session_id


# --------------------------------------------------
# Chat history
# --------------------------------------------------

if "messages" not in st.session_state:

    try:

        response = requests.get(
            f"{FASTAPI_URL}/chat-history",
            params={
                "session_id": (
                    st.session_state.session_id
                )
            },
            timeout=10
        )

        if response.status_code == 200:

            st.session_state.messages = (
                response.json().get(
                    "messages",
                    []
                )
            )

        else:

            st.session_state.messages = []

    except requests.exceptions.RequestException:

        st.session_state.messages = []


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.title("📄 Documents")


    # --------------------------------------------------
    # Upload PDF
    # --------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"]
    )


    if uploaded_file is not None:

        if st.button(
            "Upload & Process",
            use_container_width=True
        ):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                )
            }


            with st.spinner(
                "Processing document, this may take a few minutes..."
            ):

                try:

                    response = requests.post(

                        f"{FASTAPI_URL}/upload",

                        params={
                            "session_id": (
                                st.session_state.session_id
                            )
                        },

                        files=files,

                        timeout=300
                    )


                    if response.status_code == 200:

                        result = response.json()


                        st.success(
                            "Document uploaded successfully!"
                        )


                    else:

                        st.error(
                            f"Upload failed: "
                            f"{response.status_code}"
                        )

                        st.code(
                            response.text
                        )


                except requests.exceptions.ConnectionError:

                    st.error(
                        "Unable to connect to FastAPI server."
                    )


                except requests.exceptions.Timeout:

                    st.error(
                        "Document processing took too long."
                    )


    st.divider()


    # --------------------------------------------------
    # Clear chat
    # --------------------------------------------------

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


# --------------------------------------------------
# Main UI
# --------------------------------------------------

st.title(
    "💬 RAG Document Assistant"
)

st.caption(
    "Upload documents and ask questions about their content."
)


# --------------------------------------------------
# Display chat history
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# --------------------------------------------------
# Chat input
# --------------------------------------------------

question = st.chat_input(
    "Ask a question about your documents..."
)


# --------------------------------------------------
# Ask question
# --------------------------------------------------

if question:

    # --------------------------------------------------
    # Save user message
    # --------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    with st.chat_message("user"):

        st.markdown(question)


    # --------------------------------------------------
    # Ask FastAPI
    # --------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                response = requests.post(

                    f"{FASTAPI_URL}/ask",

                    json={
                        "question": question,

                        "session_id": (
                            st.session_state.session_id
                        )
                    },

                    timeout=300
                )


                if response.status_code == 200:

                    result = response.json()

                    answer = result.get(
                        "answer",
                        "I couldn't generate an answer."
                    )


                else:

                    answer = (
                        f"Request failed "
                        f"({response.status_code})."
                    )

                    st.code(
                        response.text
                    )


            except requests.exceptions.ConnectionError:

                answer = (
                    "Unable to connect to the FastAPI server."
                )


            except requests.exceptions.Timeout:

                answer = (
                    "The request took too long. "
                    "Please try again."
                )


        # --------------------------------------------------
        # Display answer
        # --------------------------------------------------

        st.markdown(answer)


        # --------------------------------------------------
        # Save assistant message
        # --------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )
