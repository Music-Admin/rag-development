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

os.environ["GOOGLE_API_KEY"] = st.secrets["google"]["api_key"]

# Function to initialize EmbedChain bot with Gemini
def embedchain_bot():
    return App.from_config(config_path="config.yaml")

# Initialize session state
if "app" not in st.session_state:
    st.session_state.app = embedchain_bot()
if "messages" not in st.session_state:
    st.session_state.messages = []

# Check if the file has already been added
if "file_added" not in st.session_state:
    with st.spinner("Loading up the Copyright Law..."):
        try:
            st.session_state.app.add("https://www.copyright.gov/title17/title17.pdf", data_type="pdf_file")
            st.session_state.file_added = True  # Track that the file has been added
            st.success("Preloaded file added to knowledge base!")
        except Exception as e:
            st.error(f"Error adding file: {e}")

# Chat Interface
st.subheader("Chat with the Copyright Law of the United States (and Related Laws Contained in Title 17 of the United States Code)")
for i, msg in enumerate(st.session_state.messages):
    message(msg["content"], is_user=msg["role"] == "user", key=str(i))

if prompt := st.chat_input("Ask a question about the Copyright Law"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True)

    with st.spinner("Thinking..."):
        response = st.session_state.app.chat(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        message(response)

# Clear Chat History
if st.button("Clear Chat History"):
    st.session_state.messages = []