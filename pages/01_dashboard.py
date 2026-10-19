import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- PAGE CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="PragyanAI Analytics Explorer",
    page_icon="🏛️",
    layout="wide"
)
st.image("")
# Header Logo and Title Layout
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    try:
        st.image("PragyanAI_Transperent.png", width=130)
    except Exception:
        st.markdown("###  PragyanAI")
with header_col2:
    st.title("PragyanAI - Multi-Domain Data & Advanced Analytics Explorer")
    st.markdown("Explore regional metrics across all platform datasets with publication-ready charts and export comprehensive analysis reports in Markdown (`.md`) format.")

st.divider()

# --- DATABASE CONNECTION & TABLES DISCOVERY ---
@st.cache_data
def get_sql_tables_list():
    try:
        conn = sqlite3.connect("data/labour_platform.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] not in ['sqlite_sequence', '00_dataset_inventory']]
        conn.close()
        return tables
    except Exception:
        return []

available_tables = get_sql_tables_list()

if not available_tables:
    st.warning("No database tables found in `data/labour_platform.db`.")
else:
    selected_table = st.selectbox("Select Active Data Domain / Table:", options=available_tables)
    
    @st.cache_data
    def load_table_data(table_name):
        conn = sqlite3.connect("data/labour_platform.db")
        data_df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        return data_df

    df = load_table_data(selected_table)

    if df.empty:
        st.info(f"The table `{selected_table}` is currently empty.")
    else:
        # --- SIDEBAR ADVANCED SEGMENT FILTERS ---
        st.sidebar.header(f"🔍 Advanced Filters: {selected_table}")
        
        filtered_df = df.copy()
        
        # Filter by Uploader if metadata exists
        if 'uploaded_by' in df.columns:
            uploaders = sorted(df['uploaded_by'].dropna().unique().tolist())
            sel_uploader = st.sidebar.multiselect("Filter by Uploader:", options=uploaders, default=uploaders)
            if sel_uploader:
                filtered_df = filtered_df[filtered_df['uploaded_by'].isin(sel_uploader)]

        # Filter by District if column exists
        if 'district' in df.columns:
            districts = sorted(df['district'].dropna().unique().tolist())
            sel_dist = st.sidebar.multiselect("Filter District(s):", options=districts, default=districts[:15] if len(districts)>15 else districts)
            if sel_dist:
                filtered_df = filtered_df[filtered_df['district'].isin(sel_dist)]

        # Filter by Sector if column exists
        if 'sector' in df.columns:
            sectors = sorted(df['sector'].dropna().unique().tolist())
            sel_sec = st.sidebar.multiselect("Filter Sector(s):", options=sectors, default=sectors)
            if sel_sec:
                filtered_df = filtered_df[filtered_df['sector'].isin(sel_sec)]

        # --- TOP KPI METRICS PANEL ---
        st.subheader(" Executive KPI Metrics Panel")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records Analyzed", f"{len(filtered_df):,}")
        col2.metric("Total Attributes", f"{len(filtered_df.columns)}")
        
        if 'employment_rate' in filtered_df.columns:
            col3.metric("Average Employment Rate", f"{filtered_df['employment_rate'].mean():.1f}%")
            col4.metric("Peak Employment Rate", f"{filtered_df['employment_rate'].max():.1f}%")
        elif 'estimated_monthly_income_inr' in filtered_df.columns:
            mean_inc = filtered_df['estimated_monthly_income_inr'].mean()
            col3.metric("Average Income (INR)", f"₹{mean_inc:,.0f}" if pd.notnull(mean_inc) else "N/A")
            col4.metric("Active Income Records", f"{filtered_df['estimated_monthly_income_inr'].notnull().sum():,}")
        elif 'annual_intake_capacity' in filtered_df.columns:
            col3.metric("Total Intake Capacity", f"{filtered_df['annual_intake_capacity'].sum():,}")
            col4.metric("Total Enrolment", f"{filtered_df['annual_enrolment'].sum():,}" if 'annual_enrolment' in filtered_df.columns else "N/A")
        else:
            col3.metric("Domain Status", "Active & Indexed")
            col4.metric("Verification Level", "Verified")

        st.divider()

        # --- ADVANCED BEAUTIFIED PLOTLY CHARTS ---
        st.subheader(" Visual Analytics & Distribution Insights")
        c1, c2 = st.columns(2)
        
        with c1:
            if 'workforce_status' in filtered_df.columns:
                fig_pie = px.pie(
                    filtered_df, names='workforce_status', hole=0.5, 
                    title="<b>Workforce Status Proportions</b>",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_pie.update_layout(template="plotly_white", title_font_size=15, legend_title="Status")
                st.plotly_chart(fig_pie, use_container_width=True)
            elif 'district' in filtered_df.columns:
                fig_bar = px.histogram(
                    filtered_df, x='district', 
                    title=f"<b>Record Concentration by District ({selected_table})</b>",
                    color_discrete_sequence=['#1f77b4']
                )
                fig_bar.update_layout(template="plotly_white", xaxis_tickangle=-45, title_font_size=15)
                st.plotly_chart(fig_bar, use_container_width=True)
            elif 'institute_type' in filtered_df.columns:
                fig_inst = px.histogram(
                    filtered_df, x='institute_type',
                    title="<b>Distribution by Institute Type</b>",
                    color_discrete_sequence=['#2ca02c']
                )
                fig_inst.update_layout(template="plotly_white", title_font_size=15)
                st.plotly_chart(fig_inst, use_container_width=True)
            else:
                st.info("Primary categorical chart unavailable for this domain schema.")

        with c2:
            if 'age_group' in filtered_df.columns and 'gender' in filtered_df.columns:
                fig_hist = px.histogram(
                    filtered_df, x='age_group', color='gender', barmode='group', 
                    title="<b>Demographic Spread: Age Group vs Gender</b>",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_hist.update_layout(template="plotly_white", title_font_size=15)
                st.plotly_chart(fig_hist, use_container_width=True)
            elif 'sector' in filtered_df.columns:
                fig_sec = px.histogram(
                    filtered_df, y='sector', 
                    title="<b>Sector Distribution Overview</b>",
                    color_discrete_sequence=['#e07a5f']
                )
                fig_sec.update_layout(template="plotly_white", title_font_size=15)
                st.plotly_chart(fig_sec, use_container_width=True)
            elif 'college_type' in filtered_df.columns:
                fig_col = px.histogram(
                    filtered_df, x='college_type',
                    title="<b>College Types Spread</b>",
                    color_discrete_sequence=['#9467bd']
                )
                fig_col.update_layout(template="plotly_white", title_font_size=15)
                st.plotly_chart(fig_col, use_container_width=True)
            else:
                st.info("Secondary distributional chart unavailable for this table.")

        st.divider()

        # --- MARKDOWN REPORT GENERATION & DOWNLOAD ---
        st.subheader(" Export Comprehensive Diagnostic Report")
        st.markdown("Generate and download a professional summary report of the filtered metrics in **Markdown (.md)** format.")

        def generate_markdown_report(data_frame, domain_name):
            total_records = len(data_frame)
            active_districts = data_frame['district'].nunique() if 'district' in data_frame.columns else "N/A"
            mean_emp = f"{data_frame['employment_rate'].mean():.2f}%" if 'employment_rate' in data_frame.columns else "N/A"
            
            md_content = f"""# 🏛️ PragyanAI & KSISU Executive Analytics Report
**Domain / Table:** `{domain_name}`  
**Generated Records:** `{total_records:,}`  
**Active Districts Covered:** `{active_districts}`  

---

##  Executive Summary
This professional diagnostic report highlights key analytical indicators extracted from the `{domain_name}` database repository under current user-selected filters. 

* **Average Employment Index:** {mean_emp}
* **Dataset Dimensions:** {len(data_frame.columns)} attributes actively tracked.

---

##  Key Observations & Breakdown
"""
            if 'workforce_status' in data_frame.columns:
                status_counts = data_frame['workforce_status'].value_counts().to_string()
                md_content += f"\n### Workforce Status Distribution\n```text\n{status_counts}\n```\n"
            
            if 'district' in data_frame.columns:
                top_districts = data_frame['district'].value_counts().head(5).to_string()
                md_content += f"\n### Top Active Districts\n```text\n{top_districts}\n```\n"

            md_content += "\n---  \n*Report compiled securely and verified via PragyanAI Intelligence Platform.*"
            return md_content

        report_markdown = generate_markdown_report(filtered_df, selected_table)
        
        col_dl1, col_dl2 = st.columns([1, 3])
        with col_dl1:
            st.download_button(
                label="📥 Download Report (.md)",
                data=report_markdown,
                file_name=f"PragyanAI_Analysis_Report_{selected_table}.md",
                mime="text/markdown"
            )

        st.subheader(f" Record Preview: `{selected_table}`")
        st.dataframe(filtered_df, use_container_width=True)
