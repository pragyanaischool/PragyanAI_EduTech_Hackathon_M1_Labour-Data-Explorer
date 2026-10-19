import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.title(" Multi-Domain Data & Advanced Analytics Explorer")
st.markdown("Explore regional metrics across domains with stylized, publication-ready charts and export comprehensive analysis reports in Markdown (.md) format.")

@st.cache_data
def get_sql_tables_list():
    try:
        conn = sqlite3.connect("data/labour_platform.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        conn.close()
        return tables
    except Exception:
        return []

available_tables = get_sql_tables_list()

if not available_tables:
    st.warning("No database tables found in `data/labour_platform.db`[cite: 2].")
else:
    selected_table = st.selectbox("Select Active Data Domain / Table:", options=available_tables)
    
    @st.cache_data
    def load_table_data(table_name):
        conn = sqlite3.connect("data/labour_platform.db")
        data_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return data_df

    df = load_table_data(selected_table)

    if df.empty:
        st.info(f"The table `{selected_table}` is empty.")
    else:
        st.sidebar.header(f"🎯 Filters: {selected_table}")
        
        filtered_df = df.copy()
        
        if 'uploaded_by' in df.columns:
            uploaders = sorted(df['uploaded_by'].dropna().unique().tolist())
            sel_uploader = st.sidebar.multiselect("Filter by Uploader:", options=uploaders, default=uploaders)
            if sel_uploader:
                filtered_df = filtered_df[filtered_df['uploaded_by'].isin(sel_uploader)]

        if 'district' in df.columns:
            districts = sorted(df['district'].dropna().unique().tolist())
            sel_dist = st.sidebar.multiselect("Filter District(s):", options=districts, default=districts[:10] if len(districts)>10 else districts)
            if sel_dist:
                filtered_df = filtered_df[filtered_df['district'].isin(sel_dist)]

        # KPI Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Records Analyzed", f"{len(filtered_df):,}")
        col2.metric("Columns Tracked", f"{len(filtered_df.columns)}")
        
        if 'employment_rate' in filtered_df.columns:
            col3.metric("Average Employment Rate", f"{filtered_df['employment_rate'].mean():.1f}%")
        else:
            col3.metric("Domain Status", "Active & Indexed")

        st.divider()

        # --- BEAUTIFIED PLOTLY CHARTS ---
        c1, c2 = st.columns(2)
        with c1:
            if selected_table == 'labour_indicators' and 'workforce_status' in filtered_df.columns:
                fig_pie = px.pie(
                    filtered_df, names='workforce_status', hole=0.5, 
                    title="<b>Workforce Status Proportions</b>",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_pie.update_layout(template="plotly_white", title_font_size=16)
                st.plotly_chart(fig_pie, use_container_width=True)
            elif 'district' in filtered_df.columns:
                fig_bar = px.histogram(
                    filtered_df, x='district', 
                    title=f"<b>Record Concentration by District ({selected_table})</b>",
                    color_discrete_sequence=['#2b5c8f']
                )
                fig_bar.update_layout(template="plotly_white", xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            if 'age_group' in filtered_df.columns and 'gender' in filtered_df.columns:
                fig_hist = px.histogram(
                    filtered_df, x='age_group', color='gender', barmode='group', 
                    title="<b>Demographic Spread: Age vs Gender</b>",
                    color_qualitative=px.colors.qualitative.Bold
                )
                fig_hist.update_layout(template="plotly_white")
                st.plotly_chart(fig_hist, use_container_width=True)
            elif 'sector' in filtered_df.columns:
                fig_sec = px.histogram(
                    filtered_df, y='sector', 
                    title="<b>Sector Distribution Overview</b>",
                    color_discrete_sequence=['#e07a5f']
                )
                fig_sec.update_layout(template="plotly_white")
                st.plotly_chart(fig_sec, use_container_width=True)

        st.divider()

        # --- MARKDOWN REPORT GENERATION & DOWNLOAD ---
        st.subheader(" Export Comprehensive Diagnostic Report")
        st.markdown("Generate and download a professional summary report of the filtered metrics in **Markdown (.md)** format.")

        def generate_markdown_report(data_frame, domain_name):
            total_records = len(data_frame)
            active_districts = data_frame['district'].nunique() if 'district' in data_frame.columns else "N/A"
            mean_emp = f"{data_frame['employment_rate'].mean():.2f}%" if 'employment_rate' in data_frame.columns else "N/A"
            
            md_content = f"""#  KSISU & KSIWAP Executive Analytics Report
**Domain / Table:** `{domain_name}`  
**Generated Records:** `{total_records:,}`  
**Active Districts Covered:** `{active_districts}`  

---

##  Executive Summary
This report highlights analytical indicators extracted from the `{domain_name}` repository under current filter configurations. 

* **Average Employment Index:** {mean_emp}
* **Dataset Dimensions:** {len(data_frame.columns)} attributes tracked.

---

##  Key Observations & Breakdown
"""
            if 'workforce_status' in data_frame.columns:
                status_counts = data_frame['workforce_status'].value_counts().to_string()
                md_content += f"\n### Workforce Status Distribution\n```text\n{status_counts}\n```\n"
            
            if 'district' in data_frame.columns:
                top_districts = data_frame['district'].value_counts().head(5).to_string()
                md_content += f"\n### Top Active Districts\n```text\n{top_districts}\n```\n"

            md_content += "\n---  \n*Report compiled securely via KSISU & KSIWAP Intelligence Platform.*"
            return md_content

        report_markdown = generate_markdown_report(filtered_df, selected_table)
        
        st.download_button(
            label=" Download Analysis Report (.md)",
            data=report_markdown,
            file_name=f"KSISU_Analysis_Report_{selected_table}.md",
            mime="text/markdown"
        )

        st.subheader(f" Record Preview: `{selected_table}`")
        st.dataframe(filtered_df, use_container_width=True)
