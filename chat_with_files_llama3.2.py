import os
import tempfile
import base64
import streamlit as st
from streamlit_chat import message
from docx import Document
import pandas as pd
from embedchain import App
from chromadb.config import Settings
from chromadb import PersistentClient

# Ensure a persistent database directory
CHROMA_DB_PATH = "./chroma_db"

# Function to initialize EmbedChain bot
def embedchain_bot():
    return App.from_config(
        config={
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": "llama3.2:latest",
                    "max_tokens": 250,
                    "temperature": 0.5,
                    "stream": True,
                    "base_url": 'http://localhost:11434',
                },
            },
            "vectordb": {
                "provider": "chroma",
                "config": {"dir": CHROMA_DB_PATH},
            },
            "embedder": {
                "provider": "ollama",
                "config": {"model": "llama3.2:latest", "base_url": 'http://localhost:11434'},
            },
        }
    )

# Display PDF in Streamlit
def display_pdf(file):
    base64_pdf = base64.b64encode(file.read()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Load DOCX file
def load_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Load CSV/Excel file
def load_csv(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception:
        df = pd.read_excel(file_path)
    return df.to_string()

# Load text file
def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Initialize session state
if "app" not in st.session_state:
    st.session_state.app = embedchain_bot()
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar - File Upload
with st.sidebar:
    st.header("Upload a File")
    file = st.file_uploader("Upload a PDF, DOCX, TXT, or CSV file", type=["pdf", "docx", "txt", "csv"])

    if file:
        # Create a temporary file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.name)

        with open(file_path, "wb") as f:
            f.write(file.getvalue())

        st.subheader("File Preview")
        file_type = file.name.split(".")[-1].lower()

        # Display the file preview
        if file_type == "pdf":
            display_pdf(file)
        elif file_type == "docx":
            st.text(load_docx(file_path))
        elif file_type in ["csv", "xlsx"]:
            st.text(load_csv(file_path))
        else:
            st.text(load_txt(file_path))

        # Add to knowledge base
        if st.button("Add to Knowledge Base"):
            with st.spinner("Adding file to knowledge base..."):
                try:
                    st.session_state.app.add(file_path, data_type=file_type)
                    st.success(f"Added {file.name} to knowledge base!")
                except Exception as e:
                    st.error(f"Error adding file: {e}")
                finally:
                    os.remove(file_path)  # Clean up temporary file

# Chat Interface
st.subheader("Chat with Your Files")
for i, msg in enumerate(st.session_state.messages):
    message(msg["content"], is_user=msg["role"] == "user", key=str(i))

if prompt := st.chat_input("Ask a question about the uploaded file"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True)

    with st.spinner("Thinking..."):
        response = st.session_state.app.chat(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        message(response)

# Clear Chat History
if st.button("Clear Chat History"):
    st.session_state.messages = []