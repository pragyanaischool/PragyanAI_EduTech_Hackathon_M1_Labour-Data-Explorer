import streamlit as st
import pandas as pd
import sqlite3
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

st.title("PragyanAI - Multi-User Data & Document Upload Portal")
st.image("")
st.markdown("Specify your user identity, select a data category, and ingest structured CSV tables directly into the SQLite database or unstructured documents into the FAISS vector repository.")

VECTOR_INDEX_DIR = "data/vector_index"

# --- USER PROFILE & METADATA SECTION ---
st.subheader("1. User Identification & Metadata")
col1, col2 = st.columns(2)
with col1:
    username = st.text_input("Username / Analyst ID:", value="researcher_user_1")
with col2:
    category = st.selectbox(
        "Data Category:",
        options=[
            "labour_indicators", 
            "district_sector_economy", 
            "college_master", 
            "training_institute_master", 
            "courses_skill_mapping",
            "training_batches_outcomes",
            "employer_master",
            "job_vacancies",
            "job_fair_events",
            "custom_user_survey"
        ]
    )

st.divider()

# --- FILE UPLOAD SECTION ---
st.subheader("2. Upload Source Files")
uploaded_file = st.file_uploader(
    f"Upload files under user profile **'{username}'**", 
    type=["csv", "txt"]
)

if uploaded_file is not None:
    file_ext = uploaded_file.name.split('.')[-1].lower()
    
    if file_ext == 'csv':
        try:
            df = pd.read_csv(uploaded_file)
            
            # Inject user and category metadata into the dataframe
            df['uploaded_by'] = username
            df['upload_category'] = category
            
            st.success(f"Parsed CSV successfully ({len(df):,} rows, {len(df.columns)} columns). User tag **'{username}'** assigned.")
            st.dataframe(df.head(5))
            
            target_table = st.text_input("Target SQLite Table Name:", value=category)
            
            if st.button(" Commit Dataset to SQL Database"):
                if target_table:
                    conn = sqlite3.connect("data/labour_platform.db")
                    df.to_sql(target_table, conn, if_exists="append", index=False)
                    conn.close()
                    st.success(f"Successfully committed data under user **{username}** into table `{target_table}`!")
                else:
                    st.warning("Please provide a valid table name.")
        except Exception as err:
            st.error(f"Error processing uploaded CSV: {err}")
            
    elif file_ext == 'txt':
        try:
            raw_text = uploaded_file.getvalue().decode("utf-8")
            st.text_area("Document Content Preview:", raw_text[:1500], height=200)
            
            if st.button(" Embed & Index Document into Vector DB"):
                with st.spinner("Generating HuggingFace sentence embeddings and updating FAISS index..."):
                    doc = Document(
                        page_content=raw_text, 
                        metadata={"filename": uploaded_file.name, "uploaded_by": username, "category": category}
                    )
                    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                    
                    if os.path.exists(VECTOR_INDEX_DIR):
                        vector_db = FAISS.load_local(VECTOR_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
                        vector_db.add_documents([doc])
                    else:
                        vector_db = FAISS.from_documents([doc], embeddings)
                        
                    vector_db.save_local(VECTOR_INDEX_DIR)
                    st.success(f"Document '{uploaded_file.name}' uploaded by **{username}** was successfully indexed into the FAISS Vector Database.")
        except Exception as err:
            st.error(f"Error embedding text document: {err}")
