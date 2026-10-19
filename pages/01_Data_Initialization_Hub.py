import streamlit as st
import os
import sqlite3
import pandas as pd
import glob
import requests
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

st.set_page_config(
    page_title="Data Initialization Hub",
    page_icon="📥",
    layout="wide"
)

# Header Logo and Branding
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    try:
        st.image("PragyanAI_Transperent.png", width=130)
    except Exception:
        st.markdown("### 🏛️ PragyanAI")
with header_col2:
    st.title("PragyanAI - Data Initialization & LLM Explanation Hub")
    st.markdown("Initialize databases, bulk-upload core platform datasets, commit records into SQLite, and explore AI-powered dataset summaries and feature explanations.")

st.divider()

EXPECTED_CSVS = [
    "00_DATASET_INVENTORY.csv",
    "01_labour_market_indicators.csv",
    "02_district_sector_economy.csv",
    "03_college_master.csv",
    "04_training_institute_master.csv",
    "05_courses_skill_mapping.csv",
    "06_training_batches_outcomes.csv",
    "07_employer_master.csv",
    "08_job_vacancies.csv",
    "09_job_fair_events.csv"
]

groq_api_key = st.secrets.get("GROQ_API_KEY", None)

# --- 1. BULK DATASET UPLOAD & DB COMMIT ---
st.subheader("🚀 Bulk Dataset Upload & Database Synchronization")
st.markdown("Select and upload all required platform CSV datasets simultaneously to initialize and populate your SQLite database tables.")

bulk_files = st.file_uploader("Select core CSV dataset files:", type=["csv"], accept_multiple_files=True)

if bulk_files:
    if st.button("🚀 Process & Commit All Files to SQLite DB"):
        with st.spinner("Processing datasets and writing to database..."):
            os.makedirs("data", exist_ok=True)
            conn = sqlite3.connect("data/labour_platform.db")
            success_count = 0
            
            for f in bulk_files:
                try:
                    save_path = os.path.join("data", f.name)
                    with open(save_path, "wb") as w:
                        w.write(f.getbuffer())
                    
                    df = pd.read_csv(save_path)
                    if 'uploaded_by' not in df.columns:
                        df['uploaded_by'] = 'system_admin'
                    df['upload_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    table_name = f.name.replace(".csv", "").lower().strip()
                    df.to_sql(table_name, conn, if_exists="replace", index=False)
                    success_count += 1
                except Exception as err:
                    st.error(f"Failed to process `{f.name}`: {err}")
                    
            conn.close()
            st.success(f"Successfully processed and committed {success_count} dataset(s) into SQLite! Refreshing...")
            st.rerun()

st.divider()

# --- 2. TABLE INSPECTION & LLM FEATURE EXPLANATIONS ---
st.subheader("🔍 Inspect Tables One-by-One & Get AI Feature Explanations")

try:
    conn = sqlite3.connect("data/labour_platform.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']
    conn.close()

    if tables:
        selected_tbl = st.selectbox("Select Active Dataset Table to Inspect:", options=tables)
        
        conn = sqlite3.connect("data/labour_platform.db")
        preview_df = pd.read_sql(f"SELECT * FROM [{selected_tbl}] LIMIT 100", conn)
        total_rows = pd.read_sql(f"SELECT COUNT(*) FROM [{selected_tbl}]", conn).iloc[0, 0]
        conn.close()

        # Metrics overview
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Selected Table", selected_tbl)
        col_m2.metric("Total Records", f"{total_rows:,}")
        col_m3.metric("Total Attributes (Columns)", f"{len(preview_df.columns)}")

        st.dataframe(preview_df, use_container_width=True)

        st.divider()

        # AI Feature & Dataset Explanation Section
        st.markdown("### 🧠 AI-Powered Feature & Dataset Breakdown")
        st.markdown("Click below to invoke the Groq LLM intelligence engine for a comprehensive functional and economic breakdown of this dataset.")

        if st.button(f"✨ Generate AI Explanation for `{selected_tbl}`"):
            if not groq_api_key:
                st.error("⚠️ `GROQ_API_KEY` is missing from `.streamlit/secrets.toml`.")
            else:
                with st.spinner(f"Analyzing schema and generating explanation for `{selected_tbl}`..."):
                    try:
                        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, groq_api_key=groq_api_key)
                        
                        col_dtypes = {col: str(dtype) for col, dtype in preview_df.dtypes.items()}
                        sample_data_snippet = preview_df.head(3).to_dict()
                        
                        prompt = f"""
You are the Chief Senior Workforce Economist and Data Architect for PragyanAI.
Analyze the dataset table named `{selected_tbl}`.
Columns and data types: {col_dtypes}
Sample data snippet: {sample_data_snippet}

Please provide a structured professional breakdown covering:
1. **Executive Dataset Overview:** What does this table model in the context of state-level workforce and education intelligence (KSISU/KSIWAP)?
2. **Detailed Feature / Column Explanation:** Describe the practical significance of key attributes.
3. **Strategic & Economic Value:** What types of policy interventions or labor market optimization decisions does this dataset unlock?
"""
                        response = llm.invoke([
                            SystemMessage(content="You are an expert workforce economist and technical data architect."),
                            HumanMessage(content=prompt)
                        ])
                        
                        st.markdown("---")
                        st.markdown(response.content)
                        st.markdown("---")
                    except Exception as llm_err:
                        st.error(f"Error generating AI explanation: {llm_err}")
    else:
        st.warning("⚠️ No database tables found in `data/labour_platform.db`. Please upload your CSV datasets above to begin.")
except Exception as e:
    st.error(f"Database error: {e}")
