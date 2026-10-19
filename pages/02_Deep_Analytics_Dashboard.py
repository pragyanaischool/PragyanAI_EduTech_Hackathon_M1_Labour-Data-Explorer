import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

st.set_page_config(
    page_title="Deep Analytics Dashboard",
    page_icon="📊",
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
    st.title("PragyanAI - Collaborative & Deep Analytics Dashboard")
    st.markdown("Explore multi-domain key analytics, extended metrics, collaborative cross-tabulations, deep statistical distributions, and AI-driven insights.")

st.divider()

groq_api_key = st.secrets.get("GROQ_API_KEY", None)

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
    st.warning("⚠️ No database tables found in `data/labour_platform.db`. Please initialize data in the **Data Initialization Hub**.")
else:
    selected_table = st.selectbox("Select Active Domain Dataset for Analysis:", options=available_tables)
    
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
        # --- SIDEBAR ADVANCED FILTERS ---
        st.sidebar.header(f"🎯 Analytics Filters: {selected_table}")
        filtered_df = df.copy()
        
        if 'district' in df.columns:
            districts = sorted(df['district'].dropna().unique().tolist())
            sel_dist = st.sidebar.multiselect("Filter District(s):", options=districts, default=districts[:15] if len(districts)>15 else districts)
            if sel_dist:
                filtered_df = filtered_df[filtered_df['district'].isin(sel_dist)]

        if 'sector' in df.columns:
            sectors = sorted(df['sector'].dropna().unique().tolist())
            sel_sec = st.sidebar.multiselect("Filter Sector(s):", options=sectors, default=sectors)
            if sel_sec:
                filtered_df = filtered_df[filtered_df['sector'].isin(sel_sec)]

        # --- MULTI-TAB ANALYTICS ARCHITECTURE ---
        tab_key, tab_more, tab_collab, tab_deep = st.tabs([
            "📈 Key Analytics", 
            "📊 More Analytics", 
            "🤝 Collaborative Analytics", 
            "🔬 Deep Analytics & AI Insights"
        ])

        # =====================================================================
        # TAB 1: KEY ANALYTICS
        # =====================================================================
        with tab_key:
            st.subheader("📈 Executive Key Analytics & Core Metrics")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Filtered Records", f"{len(filtered_df):,}")
            c2.metric("Total Attributes", f"{len(filtered_df.columns)}")
            
            if 'employment_rate' in filtered_df.columns:
                c3.metric("Avg Employment Rate", f"{filtered_df['employment_rate'].mean():.1f}%")
                c4.metric("Peak Employment Rate", f"{filtered_df['employment_rate'].max():.1f}%")
            elif 'estimated_monthly_income_inr' in filtered_df.columns:
                mean_inc = filtered_df['estimated_monthly_income_inr'].mean()
                c3.metric("Average Income", f"₹{mean_inc:,.0f}" if pd.notnull(mean_inc) else "N/A")
                c4.metric("Active Records", f"{filtered_df['estimated_monthly_income_inr'].notnull().sum():,}")
            else:
                c3.metric("Domain Status", "Active & Indexed")
                c4.metric("Verification", "Verified")

            st.divider()
            
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                if 'workforce_status' in filtered_df.columns:
                    fig_k1 = px.pie(filtered_df, names='workforce_status', hole=0.5, title="<b>Workforce Status Proportions</b>", color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_k1.update_layout(template="plotly_white")
                    st.plotly_chart(fig_k1, use_container_width=True)
                elif 'district' in filtered_df.columns:
                    fig_k1 = px.histogram(filtered_df, x='district', title=f"<b>Record Concentration by District</b>", color_discrete_sequence=['#1f77b4'])
                    fig_k1.update_layout(template="plotly_white", xaxis_tickangle=-45)
                    st.plotly_chart(fig_k1, use_container_width=True)
            with col_k2:
                if 'sector' in filtered_df.columns:
                    fig_k2 = px.histogram(filtered_df, y='sector', title="<b>Sector Concentration Overview</b>", color_discrete_sequence=['#e07a5f'])
                    fig_k2.update_layout(template="plotly_white")
                    st.plotly_chart(fig_k2, use_container_width=True)

        # =====================================================================
        # TAB 2: MORE ANALYTICS
        # =====================================================================
        with tab_more:
            st.subheader("📊 Extended Distributional Analytics")
            st.markdown("Detailed breakdown of secondary categorical distributions and operational capacities.")
            
            m1, m2 = st.columns(2)
            with m1:
                if 'institute_type' in filtered_df.columns:
                    fig_m1 = px.histogram(filtered_df, x='institute_type', title="<b>Distribution by Institute Type</b>", color_discrete_sequence=['#2ca02c'])
                    fig_m1.update_layout(template="plotly_white")
                    st.plotly_chart(fig_m1, use_container_width=True)
                elif 'college_type' in filtered_df.columns:
                    fig_m1 = px.histogram(filtered_df, x='college_type', title="<b>College Types Spread</b>", color_discrete_sequence=['#9467bd'])
                    fig_m1.update_layout(template="plotly_white")
                    st.plotly_chart(fig_m1, use_container_width=True)
            with m2:
                if 'ownership' in filtered_df.columns:
                    fig_m2 = px.pie(filtered_df, names='ownership', hole=0.4, title="<b>Ownership Breakdown (Public vs Private)</b>", color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_m2.update_layout(template="plotly_white")
                    st.plotly_chart(fig_m2, use_container_width=True)

        # =====================================================================
        # TAB 3: COLLABORATIVE ANALYTICS
        # =====================================================================
        with tab_collab:
            st.subheader("🤝 Collaborative Cross-Tabular Analytics")
            st.markdown("Investigate multi-variable relationships and cohort intersections across demographics and regional sectors.")
            
            if 'age_group' in filtered_df.columns and 'gender' in filtered_df.columns:
                fig_c1 = px.histogram(filtered_df, x='age_group', color='gender', barmode='group', title="<b>Collaborative Cohort Spread: Age Group vs Gender</b>", color_discrete_sequence=px.colors.qualitative.Bold)
                fig_c1.update_layout(template="plotly_white")
                st.plotly_chart(fig_c1, use_container_width=True)
            else:
                st.info("Collaborative demographic attributes (age_group / gender) not present in this selected table schema.")

        # =====================================================================
        # TAB 4: DEEP ANALYTICS & AI INSIGHTS
        # =====================================================================
        with tab_deep:
            st.subheader("🔬 Deep Statistical Analytics & AI Economic Insights")
            st.markdown("Examine wage outliers, numerical variance, and generate automated AI policy insights.")
            
            if 'estimated_monthly_income_inr' in filtered_df.columns or 'median_monthly_wage_inr' in filtered_df.columns:
                wage_col = 'estimated_monthly_income_inr' if 'estimated_monthly_income_inr' in filtered_df.columns else 'median_monthly_wage_inr'
                fig_box = px.box(filtered_df, x='sector' if 'sector' in filtered_df.columns else 'district', y=wage_col, title=f"<b>Deep Wage / Income Outlier Spread ({wage_col})</b>", color_discrete_sequence=['#2a9d8f'])
                fig_box.update_layout(template="plotly_white", xaxis_tickangle=-45)
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.info("Numerical wage/income attributes not present in this table schema.")

            st.divider()
            st.markdown("### ✨ Generate AI-Driven Deep Analytics Insights")
            
            if st.button("🤖 Run Groq LLM Deep Economic Analysis"):
                if not groq_api_key:
                    st.error("⚠️ `GROQ_API_KEY` is missing from `.streamlit/secrets.toml`.")
                else:
                    with st.spinner("Synthesizing statistical summaries and querying Groq LLM..."):
                        try:
                            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, groq_api_key=groq_api_key)
                            stats_summary = filtered_df.describe(include='all').to_string()
                            
                            prompt = f"""
You are the Chief Senior Workforce Economist for PragyanAI.
Analyze the statistical summary of the dataset table `{selected_table}` below:

{stats_summary[:3000]}

Provide a deep analytical report covering:
1. **Structural Patterns & Anomalies:** What do the statistical spreads and variances reveal?
2. **Collaborative Gaps:** Potential skill or regional mismatches.
3. **Prescriptive Policy Recommendations:** 3 actionable interventions for state policymakers (KSISU/KSIWAP).
"""
                            response = llm.invoke([
                                SystemMessage(content="You are an expert workforce economist and senior data strategist."),
                                HumanMessage(content=prompt)
                            ])
                            
                            st.markdown("---")
                            st.markdown(response.content)
                            st.markdown("---")
                        except Exception as ai_err:
                            st.error(f"Error during AI analysis: {ai_err}")
