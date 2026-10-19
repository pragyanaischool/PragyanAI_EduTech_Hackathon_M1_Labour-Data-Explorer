import streamlit as st
import os
import sqlite3
import pandas as pd
import glob
import requests
from datetime import datetime

st.set_page_config(
    page_title="PragyanAI Unified Platform",
    page_icon="🏛️",
    layout="wide"
)

# Header Logo and Branding
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    try:
        st.image("PragyanAI_Transperent.png", width=140)
    except Exception:
        st.markdown("### 🏛️ PragyanAI Platform")
with header_col2:
    st.title("PragyanAI - Unified Data Platform & Start Hub")
    st.markdown("Welcome to the enterprise workforce intelligence hub. Automatically ingest, process, and synchronize all platform datasets into SQLite below.")

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

@st.cache_resource
def init_system_databases():
    os.makedirs("data", exist_ok=True)
    db_path = "data/labour_platform.db"
    conn = sqlite3.connect(db_path)
    
    # Discover and load all CSV datasets into SQLite tables
    csv_files = glob.glob("*.csv") + glob.glob("data/*.csv")
    csv_files = list(set(csv_files))
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        table_name = filename.replace(".csv", "").lower().strip()
        try:
            df = pd.read_csv(file_path)
            if 'uploaded_by' not in df.columns:
                df['uploaded_by'] = 'system_admin'
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
                
    conn.close()

init_system_databases()

# --- START PAGE: SYSTEM HEALTH & BULK UPLOAD HUB ---
st.subheader("📁 System Status & Bulk File Ingestion Hub")

try:
    conn = sqlite3.connect("data/labour_platform.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    active_tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']
    
    if active_tables:
        st.success(f"✅ Database Connected! **{len(active_tables)} tables** currently active in `data/labour_platform.db`.")
        
        table_summary = []
        for t in active_tables:
            cnt_df = pd.read_sql(f"SELECT COUNT(*) as cnt FROM [{t}]", conn)
            table_summary.append({"Table Name": t, "Row Count": cnt_df['cnt'].iloc[0]})
        conn.close()
        
        with st.expander("📊 View Active Database Tables Summary", expanded=False):
            st.dataframe(pd.DataFrame(table_summary), use_container_width=True)
    else:
        st.warning("⚠️ No active tables found in SQLite database. Please upload your datasets below.")
        conn.close()
except Exception as e:
    st.error(f"Database connection error: {e}")

st.divider()

# --- BULK UPLOAD MULTIPLE DATASETS ---
st.subheader("📥 Bulk Upload All Required Platform Datasets")
st.markdown("Select and upload multiple CSV dataset files at once to automatically initialize and populate your SQLite database tables.")

bulk_files = st.file_uploader("Select CSV dataset files:", type=["csv"], accept_multiple_files=True)

if bulk_files:
    if st.button("🚀 Process & Commit All Files to Database"):
        with st.spinner("Processing and committing datasets to SQLite..."):
            os.makedirs("data", exist_ok=True)
            conn = sqlite3.connect("data/labour_platform.db")
            success_count = 0
            
            for up_file in bulk_files:
                try:
                    save_path = os.path.join("data", up_file.name)
                    with open(save_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    
                    df = pd.read_csv(save_path)
                    if 'uploaded_by' not in df.columns:
                        df['uploaded_by'] = 'system_admin'
                    df['upload_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    table_name = up_file.name.replace(".csv", "").lower().strip()
                    df.to_sql(table_name, conn, if_exists="replace", index=False)
                    success_count += 1
                except Exception as err:
                    st.error(f"Failed to process {up_file.name}: {err}")
                    
            conn.close()
            st.success(f"Successfully processed and committed {success_count} file(s) into the database! Refreshing...")
            st.rerun()

# --- SIDEBAR: QUICK INGESTION WIDGET ---
st.sidebar.markdown("### 🏛️ PragyanAI Platform Hub")
st.sidebar.markdown("Use the navigation links above to explore the Data Initialization Hub, Deep Analytics Dashboard, User Upload Portal, or AI Chatbot.")

st.sidebar.divider()
st.sidebar.markdown("### 📥 Quick Single Data Ingestion")
with st.sidebar.form("quick_upload_form", clear_on_submit=True):
    uploader_name = st.text_input("Analyst Name:", value="admin_analyst")
    target_tbl = st.text_input("Target Table Name:", value="custom_user_data")
    uploaded_file = st.file_uploader("Upload CSV/Excel:", type=["csv", "xlsx"])
    submitted = st.form_submit_button("Process & Dump to DB")
    
    if submitted and uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                ingest_df = pd.read_csv(uploaded_file)
            else:
                ingest_df = pd.read_excel(uploaded_file)
            
            # Process & Clean Headers
            ingest_df.columns = [str(c).strip().lower().replace(" ", "_") for c in ingest_df.columns]
            ingest_df['uploaded_by'] = uploader_name
            ingest_df['upload_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Dump to SQLite Database
            conn = sqlite3.connect("data/labour_platform.db")
            ingest_df.to_sql(target_tbl, conn, if_exists="append", index=False)
            conn.close()
            
            st.sidebar.success(f"Successfully processed {len(ingest_df):,} rows into `{target_tbl}`!")
        except Exception as err:
            st.sidebar.error(f"Ingestion failed: {err}")

# --- MISSING DATA CHECK & RECOVERY FALLBACK ---
def check_missing_files():
    existing_files = [os.path.basename(f) for f in glob.glob("*.csv") + glob.glob("data/*.csv")]
    return [c for c in EXPECTED_CSVS if c not in existing_files]

missing_files = check_missing_files()

if missing_files:
    st.warning(f"⚠️ Notice: {len(missing_files)} core dataset file(s) are missing from the local repository.")
    with st.expander("📥 Resolve Missing Datasets (Direct Upload or Google Drive Link)", expanded=True):
        st.markdown("You can upload missing CSV files directly or import them via a shared public Google Drive download link.")
        
        uploaded_missing = st.file_uploader("Upload missing CSV dataset(s):", type=["csv"], accept_multiple_files=True)
        if uploaded_missing:
            for up_file in uploaded_missing:
                save_path = os.path.join("data", up_file.name)
                with open(save_path, "wb") as f:
                    f.write(up_file.getbuffer())
            st.success("Files successfully uploaded! Refreshing application...")
            st.rerun()

        st.divider()
        
        gdrive_link = st.text_input("Paste Google Drive Shared CSV File Link:")
        target_csv_name = st.selectbox("Select which dataset this link corresponds to:", options=missing_files)
        
        if st.button("🔗 Download and Import from Google Drive"):
            if gdrive_link:
                try:
                    if "drive.google.com" in gdrive_link:
                        file_id = gdrive_link.split("/")[-2] if "file/d/" in gdrive_link else gdrive_link.split("id=")[-1]
                        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    else:
                        download_url = gdrive_link
                        
                    response = requests.get(download_url)
                    if response.status_code == 200:
                        save_path = os.path.join("data", target_csv_name)
                        with open(save_path, "wb") as f:
                            f.write(response.content)
                        st.success(f"Successfully downloaded `{target_csv_name}`! Refreshing...")
                        st.rerun()
                    else:
                        st.error("Failed to download. Ensure the Google Drive link permission is set to 'Anyone with the link can view'.")
                except Exception as e:
                    st.error(f"Download error: {e}")
