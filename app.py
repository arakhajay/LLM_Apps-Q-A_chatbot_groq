import streamlit as st
import pdfplumber
import requests
import os
from typing import List
import tempfile

# ========== SETUP ==========
st.set_page_config(page_title="Chatbot with Files + Web", layout="wide")
st.title("🤖 Q&A Chatbot with Files + Internet  🌐")

# ======== API KEY ==========
groq_api_key = st.sidebar.text_input("🔑 Enter your Groq API Key", type="password")

# ========== FILE UPLOAD ==========
uploaded_files = st.sidebar.file_uploader("📂 Upload files (PDF/Text)", accept_multiple_files=True)

def extract_text_from_files(files) -> str:
    full_text = ""
    for file in files:
        if file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
        else:
            full_text += file.read().decode("utf-8") + "\n"
    return full_text.strip()

# Extracted knowledge base
kb_text = extract_text_from_files(uploaded_files) if uploaded_files else ""

# ========== MEMORY ==========
if "history" not in st.session_state:
    st.session_state["history"] = []

# ========== CHAT FUNCTION ==========
def query_groq(prompt: str, system: str = "") -> str:
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": system}] if system else []
    for user, bot in st.session_state["history"]:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": bot})
    messages.append({"role": "user", "content": prompt})

    body = {
        "messages": messages,
        "model": "llama3-70b-8192",
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
    result = response.json()
    return result['choices'][0]['message']['content']

# ========== OPTIONAL WEB SEARCH ==========
def search_web(query: str) -> str:
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1"
        r = requests.get(url)
        data = r.json()
        abstract = data.get("AbstractText") or data.get("Answer") or "No web info found."
        return abstract
    except:
        return "Unable to search the web right now."

# ========== CHAT INPUT ==========
prompt = st.chat_input("Ask me anything!")

if prompt and groq_api_key:
    with st.spinner("Thinking..."):
        context = ""
        if kb_text:
            context += f"Knowledge from uploaded files:\n{kb_text}\n\n"
        if "search" in prompt.lower():
            web_info = search_web(prompt)
            context += f"Web info:\n{web_info}\n\n"
        system_prompt = f"You are a helpful assistant. Use the provided context to answer accurately.\n\n{context}"

        answer = query_groq(prompt, system_prompt)
        st.session_state["history"].append((prompt, answer))

# ========== CHAT HISTORY ==========
for user, bot in st.session_state["history"]:
    with st.chat_message("user"):
        st.markdown(user)
    with st.chat_message("assistant"):
        st.markdown(bot)