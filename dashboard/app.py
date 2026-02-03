
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Helper function to load events since we can't easily import from src in Streamlit without path hacking or installing as package
# Ideally we'd import get_key_events from src.utils
def get_key_events_local():
    events_data = [
        {'date': '2020-01-01', 'event': 'NBE Directives (Non-banks)', 'category': 'Regulation'},
        {'date': '2020-06-01', 'event': 'Digital Ethiopia 2025', 'category': 'Policy'},
        {'date': '2021-05-11', 'event': 'Telebirr Launch', 'category': 'Product'},
        {'date': '2023-08-01', 'event': 'M-Pesa Launch', 'category': 'Product'},
        {'date': '2025-06-01', 'event': 'Mandatory Digital Pay', 'category': 'Regulation'},
        {'date': '2025-10-01', 'event': 'EthSwitch Interoperability', 'category': 'Infrastructure'}
    ]
    df = pd.DataFrame(events_data)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    return df

# Set page config
st.set_page_config(page_title="Ethiopia Financial Inclusion Dashboard", layout="wide")

# Title
st.title("🇪🇹 Ethiopia Financial Inclusion Dashboard")

# Navigation
page = st.sidebar.radio("Navigation", ["Overview", "Access vs. Usage", "Channel Comparison", "Event Timeline", "Inclusion Projections"])

# Data Loading
@st.cache_data
def load_forecast_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, '../data/reportdata/summaries/forecast_results.csv')
    if os.path.exists(data_path):
        return pd.read_csv(data_path)
    return pd.DataFrame()

@st.cache_data
def load_raw_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming we have access to the processed/enriched data or unified data
    # Fallback to unified if enriched not explicitly saved as CSV by previous steps (we mostly worked in notebooks)
    data_path = os.path.join(current_dir, '../data/raw/ethiopia_fi_unified_data.csv')
    if os.path.exists(data_path):
        return pd.read_csv(data_path)
    return pd.DataFrame()

df_forecast = load_forecast_data()
df_raw = load_raw_data()
events_df = get_key_events_local()

# --- Page: Overview ---
if page == "Overview":
    st.header("Executive Summary")
    st.markdown("""
    **Vision:** Increase financial inclusion to 70% by 2025 (NFIS II).
    
    This dashboard monitors progress across three pillars:
    1.  **Access:** Availability of formal financial points (Accounts, Wallets).
    2.  **Usage:** Depth of adoption (Transaction volumes, P2P).
    3.  **Quality:** Relevance and affordability of services.
    """)
    
    # KPIs
    if not df_forecast.empty:
        latest = df_forecast[df_forecast['type'] == 'Historical']['year'].max()
        acc_own = df_forecast[(df_forecast['indicator']=='ACC_OWNERSHIP') & (df_forecast['year']==latest)]
        if not acc_own.empty:
            st.metric("Account Ownership", f"{acc_own['final_value'].values[0]:.1f}%", f"Year: {latest}")
    
    st.info("Navigate using the sidebar to explore specific dimensions.")

# --- Page: Access vs Usage ---
elif page == "Access vs. Usage":
    st.header("Access vs. Usage")
    st.write("Comparing the availability of accounts against active usage metrics.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Account Ownership Trend")
        if not df_raw.empty:
            acc = df_raw[df_raw['indicator_code'] == 'ACC_OWNERSHIP']
            fig_acc = px.line(acc, x='observation_date', y='value_numeric', title="Account Ownership (%)", markers=True)
            st.plotly_chart(fig_acc, use_container_width=True)
            
    with col2:
        st.subheader("Mobile Money Usage")
        if not df_raw.empty:
            # Try to find a usage indicator
            usg = df_raw[df_raw['indicator_code'].isin(['USG_P2P_VALUE', 'ACC_MM_ACCOUNT'])]
            if not usg.empty:
                fig_usg = px.line(usg, x='observation_date', y='value_numeric', color='indicator_code', 
                                  title="Usage Indicators", markers=True)
                st.plotly_chart(fig_usg, use_container_width=True)

# --- Page: Channel Comparison ---
elif page == "Channel Comparison":
    st.header("Channel Comparison")
    st.write("Adoption rates by financial channel.")
    
    if not df_raw.empty:
        # Filter for relevant indicators
        channels = ['ACC_OWNERSHIP', 'ACC_MM_ACCOUNT']
        df_channels = df_raw[df_raw['indicator_code'].isin(channels)]
        
        fig_ch = px.bar(df_channels, x='observation_date', y='value_numeric', color='indicator_code', 
                        barmode='group', title="Traditional Accounts vs. Mobile Money")
        st.plotly_chart(fig_ch, use_container_width=True)

# --- Page: Event Timeline ---
elif page == "Event Timeline":
    st.header("Strategic Timeline")
    st.write("Key policy and market events shaping the financial landscape.")
    
    # Plotly Timeline
    # We'll use a scatter plot with dates on X and dummy Y, text labels
    events_df['y'] = 1
    
    fig_time = px.scatter(events_df, x='date', y='y', color='category', 
                          hover_data=['event'], size_max=15, 
                          title="Key Financial Inclusion Events")
    
    # Add text labels
    for i, row in events_df.iterrows():
        fig_time.add_annotation(x=row['date'], y=1, text=row['event'], yshift=10 + (i%2)*20, showarrow=False) # Stagger
    
    fig_time.update_yaxes(visible=False, showticklabels=False)
    fig_time.update_layout(height=300)
    
    st.plotly_chart(fig_time, use_container_width=True)
    st.dataframe(events_df[['date', 'event', 'category']].sort_values('date'))

# --- Page: Inclusion Projections ---
elif page == "Inclusion Projections":
    st.header("🎯 Inclusion Projections & Targets")
    
    # Configuration
    st.subheader("Scenario Configuration")
    scenario = st.radio("Select Growth Scenario", ["Baseline", "Optimistic", "Pessimistic"], horizontal=True)
    
    target_val = 70.0 # NFIS II Target
    
    if not df_forecast.empty:
        # Filter for Account Ownership primarily
        # Assuming ACC_OWNERSHIP is the main KPI for the 70% target
        proj_data = df_forecast[(df_forecast['indicator'] == 'ACC_OWNERSHIP') & 
                               ((df_forecast['scenario'] == scenario) | (df_forecast['type'] == 'Historical'))]
        
        # Deduplicate historical if present in multiple scenario rows
        proj_data = proj_data.drop_duplicates(subset=['year'])
        
        fig_proj = go.Figure()
        
        # Main Line
        fig_proj.add_trace(go.Scatter(x=proj_data['year'], y=proj_data['final_value'], 
                                      mode='lines+markers', name=f'{scenario} Projection',
                                      line=dict(width=3)))
        
        # Target Line
        fig_proj.add_hline(y=target_val, line_dash="dash", line_color="green", annotation_text="NFIS II Target (70%)")
        
        # Confidence Interval (if Baseline)
        if scenario == 'Baseline' and 'upper_ci' in proj_data.columns:
             fig_proj.add_trace(go.Scatter(x=proj_data['year'], y=proj_data['upper_ci'], mode='lines', line=dict(width=0), showlegend=False))
             fig_proj.add_trace(go.Scatter(x=proj_data['year'], y=proj_data['lower_ci'], mode='lines', line=dict(width=0), 
                                           fill='tonexty', fillcolor='rgba(0,100,80,0.2)', name='95% CI'))

        fig_proj.update_layout(title="Projected Account Ownership vs. Target", xaxis_title="Year", yaxis_title="Ownership (%)")
        st.plotly_chart(fig_proj, use_container_width=True)
        
        # Explanatory Text
        st.markdown("### Analysis")
        if scenario == "Optimistic":
            st.success("In the **Optimistic** scenario, driven by rapid interoperability adoption (EthSwitch) and foreign bank entry, we project exceeding the 70% target by 2029.")
        elif scenario == "Pessimistic":
            st.error("The **Pessimistic** scenario assumes regulatory bottlenecks. Under these conditions, the 70% target may be delayed beyond 2030.")
        else:
            st.info("The **Baseline** forecast follows current linear trends. While growth is steady, additional policy interventions may be needed to close the gap to 70% faster.")

st.markdown("---")
st.caption("v2.0 | Enhanced Interactive Dashboard")
