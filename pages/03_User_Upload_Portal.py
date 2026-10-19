import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# --- PAGE CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="User Data & Document Upload Portal",
    page_icon="📁",
    layout="wide"
)

# Header Logo and Title Layout
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    try:
        st.image("PragyanAI_Transperent.png", width=130)
    except Exception:
        st.markdown("### 🏛️ PragyanAI")
with header_col2:
    st.title("PragyanAI - Multi-User Data & Document Upload Portal")
    st.markdown("Specify your user identity, select a data category, and ingest structured CSV/Excel tables directly into SQLite or unstructured documents into FAISS vector storage.")

st.divider()

VECTOR_INDEX_DIR = "data/vector_index"

# --- 1. USER PROFILE & METADATA SECTION ---
st.subheader("1. User Identification & Metadata")
col1, col2 = st.columns(2)
with col1:
    username = st.text_input("Username / Analyst ID:", value="researcher_user_1")
with col2:
    category = st.selectbox(
        "Data Category / Domain:",
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

# --- 2. FILE UPLOAD SECTION ---
st.subheader("2. Upload Source Files (Tabular or Unstructured Text)")
uploaded_file = st.file_uploader(
    f"Upload files under user profile **'{username}'**", 
    type=["csv", "xlsx", "txt"]
)

if uploaded_file is not None:
    file_ext = uploaded_file.name.split('.')[-1].lower()
    
    # --- TABULAR INGESTION (CSV / EXCEL) ---
    if file_ext in ['csv', 'xlsx']:
        try:
            if file_ext == 'csv':
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Normalize column headers and inject audit metadata
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            df['uploaded_by'] = username
            df['upload_category'] = category
            df['upload_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            st.success(f"Parsed file successfully (`{uploaded_file.name}`): {len(df):,} rows, {len(df.columns)} columns. User tag **'{username}'** assigned.")
            st.dataframe(df.head(5), use_container_width=True)
            
            target_table = st.text_input("Target SQLite Table Name:", value=category)
            
            if st.button("📥 Commit Dataset to SQLite Database"):
                if target_table:
                    os.makedirs("data", exist_ok=True)
                    conn = sqlite3.connect("data/labour_platform.db")
                    df.to_sql(target_table, conn, if_exists="append", index=False)
                    conn.close()
                    st.success(f"Successfully committed {len(df):,} records under user **{username}** into SQLite table `{target_table}`!")
                else:
                    st.warning("Please provide a valid SQLite table name.")
        except Exception as err:
            st.error(f"Error processing uploaded tabular file: {err}")
            
    # --- UNSTRUCTURED TEXT INGESTION & VECTOR INDEXING ---
    elif file_ext == 'txt':
        try:
            raw_text = uploaded_file.getvalue().decode("utf-8")
            st.text_area("Document Content Preview:", raw_text[:1500], height=200)
            
            if st.button("🧠 Embed & Index Document into FAISS Vector DB"):
                with st.spinner("Generating HuggingFace sentence embeddings and updating FAISS vector index..."):
                    doc = Document(
                        page_content=raw_text, 
                        metadata={"filename": uploaded_file.name, "uploaded_by": username, "category": category}
                    )
                    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                    
                    os.makedirs(VECTOR_INDEX_DIR, exist_ok=True)
                    if os.path.exists(os.path.join(VECTOR_INDEX_DIR, "index.faiss")):
                        vector_db = FAISS.load_local(VECTOR_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
                        vector_db.add_documents([doc])
                    else:
                        vector_db = FAISS.from_documents([doc], embeddings)
                        
                    vector_db.save_local(VECTOR_INDEX_DIR)
                    st.success(f"Document `{uploaded_file.name}` uploaded by **{username}** was successfully embedded and indexed into the FAISS Vector Database.")
        except Exception as err:
            st.error(f"Error embedding text document: {err}")

st.divider()

# --- 3. ACTIVE DATABASE TABLES OVERVIEW ---
st.subheader("📋 Active Database Tables Overview")
try:
    conn = sqlite3.connect("data/labour_platform.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']
    
    if tables:
        summary_data = []
        for t in tables:
            cnt_df = pd.read_sql(f"SELECT COUNT(*) as cnt FROM [{t}]", conn)
            summary_data.append({"Table Name": t, "Total Rows": cnt_df['cnt'].iloc[0]})
        conn.close()
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    else:
        st.info("No active tables found in database.")
        conn.close()
except Exception as e:
    st.info(f"Database currently uninitialized: {e}")
