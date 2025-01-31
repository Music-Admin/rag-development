from embedchain import App
import os
import tempfile
import base64
import streamlit as st
from streamlit_chat import message
from docx import Document
import pandas as pd
import hashlib

# Define the embedchain_bot function
def embedchain_bot(db_path):
    return App.from_config(
        config={
            "llm": {"provider": "ollama", "config": {"model": "llama3.2:latest", "max_tokens": 250, "temperature": 0.5, "stream": True, "base_url": 'http://localhost:11434'}},
            "vectordb": {"provider": "chroma", "config": {"dir": db_path}},
            "embedder": {"provider": "ollama", "config": {"model": "llama3.2:latest", "base_url": 'http://localhost:11434'}},
        }
    )

# Add a function to display PDF
def display_pdf(file):
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Function to load DOCX files
def load_docx(file_path):
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to load CSV/Excel files
def load_csv(file_path):
    # Try reading CSV first
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception:
        # If not CSV, try reading Excel
        df = pd.read_excel(file_path)
        return df.to_string()

# Function to load text files
def load_txt(file_path):
    with open(file_path, "r") as file:
        return file.read()

# Define the database path
db_path = tempfile.mkdtemp()

# Create a session state to store the app instance and chat history
if 'app' not in st.session_state:
    st.session_state.app = embedchain_bot(db_path)
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar for file upload and preview
with st.sidebar:
    st.header("Upload a file")
    file = st.file_uploader("Upload a PDF, DOCX, TXT or CSV file", type=["pdf", "docx", "txt", "csv"])

    if file:
        file_path = tempfile.NamedTemporaryFile(delete=False)
        file_path.write(file.getvalue())
        st.subheader("File Preview")

        # Display file type
        file_type = file.name.split(".")[-1].lower()

        # Show file preview based on type
        if file_type == "pdf":
            display_pdf(file)
        elif file_type == "docx":
            st.text(load_docx(file_path.name))
        elif file_type == "csv":
            st.text(load_csv(file_path.name))
        else:
            st.text(load_txt(file_path.name))

        if st.button("Add to Knowledge Base"):
            with st.spinner("Adding file to knowledge base..."):
                if file_type == "pdf":
                    st.session_state.app.add(file_path.name, data_type="pdf_file")
                elif file_type == "docx":
                    st.session_state.app.add(file_path.name, data_type="docx")
                elif file_type == "csv":
                    st.session_state.app.add(file_path.name, data_type="csv")
                else:
                    st.session_state.app.add(file_path.name, data_type="txt")
                os.remove(file_path.name)
            st.success(f"Added {file.name} to knowledge base!")

# Chat interface
for i, msg in enumerate(st.session_state.messages):
    message(msg["content"], is_user=msg["role"] == "user", key=str(i))

if prompt := st.chat_input("Ask a question about the uploaded file"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True)

    with st.spinner("Thinking..."):
        response = st.session_state.app.chat(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        message(response)

# Clear chat history button
if st.button("Clear Chat History"):
    st.session_state.messages = []