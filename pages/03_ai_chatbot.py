import streamlit as st
import os
import sqlite3
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

st.title(" Deep Insight Analytics Chatbot (Groq RAG)")
st.markdown("Ask advanced analytical questions across all active platform databases and user document archives[cite: 1, 2].")

VECTOR_INDEX_DIR = "data/vector_index"

# Read Groq key from secrets
groq_api_key = None
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error(" `GROQ_API_KEY` missing from `.streamlit/secrets.toml`.")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask for deep insights, trend analysis, or regional recommendations..."):
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        if not groq_api_key:
            reply_string = " Groq API key configuration missing."
            st.markdown(reply_string)
        else:
            try:
                with st.spinner("Retrieving RAG context & querying Groq LLM..."):
                    # 1. Retrieve FAISS context
                    retrieved_context = ""
                    if os.path.exists(VECTOR_INDEX_DIR):
                        hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                        faiss_store = FAISS.load_local(VECTOR_INDEX_DIR, hf_embeddings, allow_dangerous_deserialization=True)
                        docs = faiss_store.similarity_search(user_input, k=3)
                        retrieved_context = "\n\n".join([f"\n{d.page_content}" for d in docs])

                    # 2. Database stats overview
                    db_overview = ""
                    try:
                        conn = sqlite3.connect("data/labour_platform.db")
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']
                        
                        summaries = []
                        for t in tables:
                            t_df = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {t}", conn)
                            summaries.append(f"- Table `{t}`: {t_df['cnt'].iloc[0]} rows")
                        conn.close()
                        db_overview = "Active Database Tables:\n" + "\n".join(summaries)
                    except Exception:
                        db_overview = "Database overview unavailable."

                    # 3. Production-Grade Deep Analytics System Prompt
                    proper_system_prompt = f"""
You are the Chief Senior Workforce Economist and Multi-Domain Data Intelligence Consultant for the KSISU and KSIWAP platform.

Your task is to analyze user questions across multiple dimensions: labour indicators, district sector economies, higher-education college databases, training institute master records[cite: 1, 2], and user uploads.

Guidelines for your response:
1. **Analytical Rigor:** Break down complex trends into clear demographic, regional, or structural components.
2. **Data Grounding:** Explicitly reference database metrics or retrieved document snippets. Do not fabricate statistics.
3. **Attribution:** Mention which user or database table supports your findings where applicable.
4. **Actionable Recommendations:** Offer concrete policy suggestions or strategic interventions.

[Platform Database Overview]:
{db_overview}

[Retrieved Document Knowledge Base]:
{retrieved_context if retrieved_context else "No custom document snippets matched this query."}
"""

                    # 4. Invoke Groq LLM
                    groq_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, groq_api_key=groq_api_key)
                    payload_messages = [SystemMessage(content=proper_system_prompt)] + [HumanMessage(content=m["content"]) for m in st.session_state.chat_messages]
                    
                    llm_response = groq_llm.invoke(payload_messages)
                    reply_string = llm_response.content
                    st.markdown(reply_string)
            except Exception as error_msg:
                reply_string = f"Error during chatbot execution: {error_msg}"
                st.error(reply_string)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": reply_string})
