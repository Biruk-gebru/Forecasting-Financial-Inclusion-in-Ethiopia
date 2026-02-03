import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Set page config
st.set_page_config(page_title="Ethiopia Financial Inclusion Forecast", layout="wide")

# Title and Introduction
st.title("🇪🇹 Ethiopia Financial Inclusion Forecasting Dashboard")
st.markdown("""
This dashboard presents historical trends and future forecasts for key financial inclusion indicators in Ethiopia.
Explore different scenarios and visualize the potential impact of various growth projections.
""")

# --- Data Loading ---
@st.cache_data
def load_data():
    # Helper to resolve path relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming the data is in ../data/reportdata/summaries/forecast_results.csv
    data_path = os.path.join(current_dir, '../data/reportdata/summaries/forecast_results.csv')
    
    if not os.path.exists(data_path):
        st.error(f"Data file not found at: {data_path}")
        return pd.DataFrame()
    
    df = pd.read_csv(data_path)
    return df

df = load_data()

if df.empty:
    st.stop()

# --- Sidebar Controls ---
st.sidebar.header("Configuration")

# Indicator Selection
indicators = df['indicator'].unique()
selected_indicator = st.sidebar.selectbox("Select Indicator", indicators, 
                                          format_func=lambda x: x.replace('_', ' ').title())

# Scenario Selection
scenarios = df['scenario'].unique()
selected_scenarios = st.sidebar.multiselect("Select Scenarios to Compare", scenarios, default=scenarios)

# Filter Data
filtered_df = df[(df['indicator'] == selected_indicator) & (df['scenario'].isin(selected_scenarios))]

# --- Main Content ---

# 1. Overview Metrics
st.subheader("📊 Forecast Overview")
col1, col2, col3 = st.columns(3)

# Calculate some metrics
# Latest Historical Value
hist_df = df[(df['indicator'] == selected_indicator) & (df['type'] == 'Historical')]
if not hist_df.empty:
    latest_hist_year = hist_df['year'].max()
    latest_hist_val = hist_df[hist_df['year'] == latest_hist_year]['final_value'].values[0]
    col1.metric("Latest Historical (2024)", f"{latest_hist_val:.2f}%")
else:
    col1.metric("Latest Historical", "N/A")

# 2025 Forecast (Baseline)
baseline_2029 = df[(df['indicator'] == selected_indicator) & 
                   (df['scenario'] == 'Baseline') & 
                   (df['year'] == 2029)]

if not baseline_2029.empty:
    val_2029 = baseline_2029['final_value'].values[0]
    delta = val_2029 - latest_hist_val
    col2.metric("2029 Projection (Baseline)", f"{val_2029:.2f}%", f"{delta:+.2f}%")
else:
    col2.metric("2029 Projection", "N/A")

# 2. Trends & Forecasts Chart
st.subheader("📈 Trends & Forecasts")

fig = go.Figure()

# Plot Historical Data (Common to all)
hist_data = df[(df['indicator'] == selected_indicator) & (df['type'] == 'Historical') & (df['scenario'] == 'Baseline')]
fig.add_trace(go.Scatter(
    x=hist_data['year'], 
    y=hist_data['final_value'],
    mode='lines+markers',
    name='Historical',
    line=dict(color='black', width=3),
    marker=dict(size=8)
))

# Plot Scenarios
colors = {'Baseline': 'blue', 'Optimistic': 'green', 'Pessimistic': 'red'}
line_styles = {'Baseline': 'dash', 'Optimistic': 'dot', 'Pessimistic': 'dot'}

for scenario in selected_scenarios:
    scen_data = filtered_df[(filtered_df['scenario'] == scenario) & (filtered_df['type'] == 'Forecast')]
    color = colors.get(scenario, 'gray')
    dash = line_styles.get(scenario, 'dash')
    
    fig.add_trace(go.Scatter(
        x=scen_data['year'], 
        y=scen_data['final_value'],
        mode='lines',
        name=f'{scenario} Forecast',
        line=dict(color=color, width=2, dash=dash)
    ))
    
    # Add Confidence Interval just for Baseline if selected
    if scenario == 'Baseline':
        # Combined dataframe including previous year to close the gap visually if desired, 
        # but for CI area we usually just show the forecast part.
        fig.add_trace(go.Scatter(
            x=scen_data['year'],
            y=scen_data['upper_ci'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=scen_data['year'],
            y=scen_data['lower_ci'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(0, 0, 255, 0.1)',
            name='95% Confidence Interval'
        ))

fig.update_layout(
    title=f"Forecast for {selected_indicator.replace('_', ' ').title()}",
    xaxis_title="Year",
    yaxis_title="Value (%)",
    legend_title="Scenario",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# 3. Data Explorer
with st.expander("📝 View Underlying Data"):
    st.dataframe(filtered_df[['year', 'type', 'scenario', 'final_value', 'lower_ci', 'upper_ci']].sort_values(by=['year', 'scenario']))
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Filtered CSV",
        csv,
        "forecast_data.csv",
        "text/csv",
        key='download-csv'
    )

st.markdown("---")
st.caption("Generated by Task 5 Forecasting Model.")
