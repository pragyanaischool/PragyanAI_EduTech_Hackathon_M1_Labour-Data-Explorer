import streamlit as st
import os
import sqlite3
import pandas as pd
import glob
import requests

st.set_page_config(
    page_title="KSISU & KSIWAP Unified Platform",
    page_icon="🏛️",
    layout="wide"
)

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
    conn = sqlite3.connect("data/labour_platform.db")
    
    # Automatically discover and load all CSV datasets into SQLite tables
    csv_files = glob.glob("data/*.csv")
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

# --- MISSING DATA CHECK & RECOVERY FALLBACK ---
def check_missing_files():
    existing_files = [os.path.basename(f) for f in glob.glob("data/*.csv")]
    return [c for c in EXPECTED_CSVS if c not in existing_files]

missing_files = check_missing_files()

if missing_files:
    st.warning(f"⚠️ Notice: {len(missing_files)} core dataset file(s) are missing from the local `data/` repository.")
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

# Multi-Page Navigation Router
pages = st.navigation({
    "Analytics Hub": [
        st.Page("pages/01_dashboard.py", title="Deep Analytics Dashboard", icon="📊"),
    ],
    "User Data Management": [
        st.Page("pages/02_file_upload.py", title="User Upload Portal", icon="📁"),
    ],
    "AI Intelligence": [
        st.Page("pages/03_ai_chatbot.py", title="Deep Insight Chatbot", icon="💬"),
    ]
})

pages.run()
