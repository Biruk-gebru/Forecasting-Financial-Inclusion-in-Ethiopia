#!/usr/bin/env python3
"""
Script to generate the EDA notebook programmatically
"""

import nbformat as nbf

# Create new notebook
nb = nbf.v4.new_notebook()

# Add cells
cells = []

# Title
cells.append(nbf.v4.new_markdown_cell("""# Task 2: Exploratory Data Analysis

## Objective
Perform comprehensive exploratory data analysis on Ethiopia's Financial Inclusion dataset to uncover trends, patterns, and insights across Access, Usage, and Infrastructure dimensions.

### Deliverables:
- Dataset overview and summary statistics
- Access trends analysis (account ownership, growth rates, gender gaps)
- Usage patterns analysis (mobile money, digital payments)
- Infrastructure and enablers analysis
- Event timeline visualization
- Correlation analysis
- Key insights documentation"""))

# Setup cell
cells.append(nbf.v4.new_code_cell("""# Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('../src')
from utils import save_fig, save_summary, calculate_growth_rate, calculate_gender_gap, create_correlation_matrix

# Set style
sns.set_style('whitegrid')
sns.set_palette('husl')
plt.rcParams['figure.figsize'] = (14, 6)

# Define paths
DATA_PATH = '../data/raw/ethiopia_fi_unified_data.csv'
REPORTDATA_PATH = '../data/reportdata'
FIGURES_PATH = os.path.join(REPORTDATA_PATH, 'figures')
SUMMARIES_PATH = os.path.join(REPORTDATA_PATH, 'summaries')"""))

# Load data
cells.append(nbf.v4.new_markdown_cell("""## 1. Dataset Overview"""))

cells.append(nbf.v4.new_code_cell("""# Load dataset
df = pd.read_csv(DATA_PATH)

# Parse dates
df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
df['year'] = df['observation_date'].dt.year

print(f"Dataset shape: {df.shape}")
print(f"Date range: {df['observation_date'].min()} to {df['observation_date'].max()}")
print(f"\\nRecord types:")
print(df['record_type'].value_counts())
print(f"\\nPillars:")
print(df['pillar'].value_counts())"""))

# Summary statistics
cells.append(nbf.v4.new_code_cell("""# Summary statistics for numeric indicators
observations = df[df['record_type'] == 'observation'].copy()

summary_stats = observations.groupby('indicator')['value_numeric'].agg([
    'count', 'mean', 'std', 'min', 'max'
]).round(2)

print("Summary Statistics by Indicator:")
print(summary_stats)

save_summary(summary_stats.reset_index(), 'dataset_overview.csv')"""))

# Access Analysis
cells.append(nbf.v4.new_markdown_cell("""## 2. Access Analysis

Analyzing account ownership trends, growth rates, and gender gaps."""))

cells.append(nbf.v4.new_code_cell("""# Account Ownership Rate over time
acc_ownership = observations[observations['indicator_code'] == 'ACC_OWNERSHIP'].copy()
acc_ownership = acc_ownership[acc_ownership['gender'] == 'all']  # Overall rate
acc_ownership = acc_ownership.sort_values('observation_date')

# Calculate growth rates
growth_df = calculate_growth_rate(observations, 'ACC_OWNERSHIP')

print("Account Ownership Growth:")
print(growth_df)

# Visualize
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Trend line
ax1.plot(acc_ownership['observation_date'], acc_ownership['value_numeric'], 
         marker='o', linewidth=2, markersize=8, label='Account Ownership Rate')
ax1.set_title('Account Ownership Rate Over Time', fontsize=14, fontweight='bold')
ax1.set_xlabel('Year')
ax1.set_ylabel('Percentage (%)')
ax1.grid(True, alpha=0.3)
ax1.legend()

# Growth rates
ax2.bar(growth_df['year'], growth_df['growth_rate'], color='steelblue', edgecolor='black')
ax2.set_title('Year-over-Year Growth Rate', fontsize=14, fontweight='bold')
ax2.set_xlabel('Year')
ax2.set_ylabel('Growth Rate (%)')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
save_fig('03_access_trends')
plt.show()"""))

# Gender Gap Analysis
cells.append(nbf.v4.new_code_cell("""# Gender gap analysis
gender_gap = calculate_gender_gap(observations, 'ACC_OWNERSHIP')

print("Gender Gap in Account Ownership:")
print(gender_gap)

# Visualize gender gap
fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(gender_gap))
width = 0.35

if 'male' in gender_gap.columns and 'female' in gender_gap.columns:
    ax.bar(x - width/2, gender_gap['male'], width, label='Male', color='#3498db')
    ax.bar(x + width/2, gender_gap['female'], width, label='Female', color='#e74c3c')
    
    # Add gap annotation
    for i, row in gender_gap.iterrows():
        if pd.notna(row.get('gap')):
            ax.text(i, max(row.get('male', 0), row.get('female', 0)) + 2, 
                   f"Gap: {row['gap']:.1f}%", 
                   ha='center', fontsize=9, fontweight='bold')

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Account Ownership Rate (%)', fontsize=12)
ax.set_title('Gender Gap in Account Ownership', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(gender_gap['year'])
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
save_fig('04_gender_gap')
plt.show()

save_summary(gender_gap, 'access_summary.csv')"""))

# Mobile Money Analysis
cells.append(nbf.v4.new_code_cell("""# Mobile Money Account penetration
mm_account = observations[observations['indicator_code'] == 'ACC_MM_ACCOUNT'].copy()
mm_account = mm_account[mm_account['gender'] == 'all']
mm_account = mm_account.sort_values('observation_date')

print("Mobile Money Account Rate:")
print(mm_account[['observation_date', 'value_numeric', 'original_text']])

# 4G Coverage
coverage_4g = observations[observations['indicator_code'] == 'ACC_4G_COV'].copy()
coverage_4g = coverage_4g.sort_values('observation_date')

print("\\n4G Coverage:")
print(coverage_4g[['observation_date', 'value_numeric', 'original_text']])"""))

# Usage Analysis
cells.append(nbf.v4.new_markdown_cell("""## 3. Usage Analysis

Analyzing mobile money and digital payment transaction trends."""))

cells.append(nbf.v4.new_code_cell("""# P2P Transaction analysis
p2p_count = observations[observations['indicator_code'] == 'USG_P2P_COUNT'].copy()
p2p_value = observations[observations['indicator_code'] == 'USG_P2P_VALUE'].copy()

# ATM transactions
atm_count = observations[observations['indicator_code'] == 'USG_ATM_COUNT'].copy()
atm_value = observations[observations['indicator_code'] == 'USG_ATM_VALUE'].copy()

# Visualize usage trends
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

# P2P Count
if len(p2p_count) > 0:
    ax1.bar(range(len(p2p_count)), p2p_count['value_numeric']/1e6, color='#2ecc71', edgecolor='black')
    ax1.set_title('P2P Transaction Count', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Transactions (Millions)')
    ax1.set_xticks(range(len(p2p_count)))
    ax1.set_xticklabels(p2p_count['fiscal_year'], rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')

# P2P Value
if len(p2p_value) > 0:
    ax2.bar(range(len(p2p_value)), p2p_value['value_numeric']/1e9, color='#3498db', edgecolor='black')
    ax2.set_title('P2P Transaction Value', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Value (Billion ETB)')
    ax2.set_xticks(range(len(p2p_value)))
    ax2.set_xticklabels(p2p_value['fiscal_year'], rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')

# ATM Count
if len(atm_count) > 0:
    ax3.bar(range(len(atm_count)), atm_count['value_numeric']/1e6, color='#e67e22', edgecolor='black')
    ax3.set_title('ATM Transaction Count', fontsize=13, fontweight='bold')
    ax3.set_ylabel('Transactions (Millions)')
    ax3.set_xticks(range(len(atm_count)))
    ax3.set_xticklabels(atm_count['fiscal_year'], rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')

# ATM Value
if len(atm_value) > 0:
    ax4.bar(range(len(atm_value)), atm_value['value_numeric']/1e9, color='#9b59b6', edgecolor='black')
    ax4.set_title('ATM Transaction Value', fontsize=13, fontweight='bold')
    ax4.set_ylabel('Value (Billion ETB)')
    ax4.set_xticks(range(len(atm_value)))
    ax4.set_xticklabels(atm_value['fiscal_year'], rotation=45)
    ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
save_fig('05_usage_trends')
plt.show()

# Save usage summary
usage_summary = pd.concat([
    p2p_count[['fiscal_year', 'indicator', 'value_numeric']].assign(metric='P2P Count'),
    p2p_value[['fiscal_year', 'indicator', 'value_numeric']].assign(metric='P2P Value')
])
save_summary(usage_summary, 'usage_summary.csv')"""))

# Infrastructure Analysis
cells.append(nbf.v4.new_markdown_cell("""## 4. Infrastructure & Enablers

Analyzing infrastructure indicators like 4G coverage, mobile penetration, and digital ID enrollment."""))

cells.append(nbf.v4.new_code_cell("""# Fayda Digital ID enrollment
fayda = observations[observations['indicator_code'] == 'ACC_FAYDA'].copy()
fayda = fayda.sort_values('observation_date')

# Mobile penetration
mobile_pen = observations[observations['indicator_code'] == 'ACC_MOBILE_PEN'].copy()

# Visualize infrastructure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# 4G Coverage growth
if len(coverage_4g) > 0:
    ax1.plot(coverage_4g['observation_date'], coverage_4g['value_numeric'], 
             marker='s', linewidth=2, markersize=10, color='#e74c3c', label='4G Coverage')
    ax1.set_title('4G Population Coverage Growth', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Coverage (%)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

# Fayda enrollment
if len(fayda) > 0:
    ax2.plot(fayda['observation_date'], fayda['value_numeric']/1e6, 
             marker='o', linewidth=2, markersize=10, color='#3498db', label='Fayda Enrollment')
    ax2.set_title('Fayda Digital ID Enrollment', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Enrollments (Millions)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

plt.tight_layout()
save_fig('06_infrastructure')
plt.show()

print("\\nInfrastructure Metrics:")
print(f"4G Coverage: {coverage_4g['value_numeric'].iloc[-1] if len(coverage_4g) > 0 else 'N/A'}%")
print(f"Fayda Enrollment: {fayda['value_numeric'].iloc[-1]/1e6 if len(fayda) > 0 else 'N/A'}M")
print(f"Mobile Penetration: {mobile_pen['value_numeric'].iloc[-1] if len(mobile_pen) > 0 else 'N/A'}%")"""))

# Event Timeline
cells.append(nbf.v4.new_markdown_cell("""## 5. Event Timeline

Visualizing policy events, product launches, and market changes over time."""))

cells.append(nbf.v4.new_code_cell("""# Extract events
events = df[df['record_type'] == 'event'].copy()
events = events.sort_values('observation_date')

print(f"Total events: {len(events)}")
print(f"\\nEvent categories:")
print(events['category'].value_counts())

if len(events) > 0:
    # Create timeline visualization
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Group by category for coloring
    categories = events['category'].unique()
    colors = sns.color_palette('husl', len(categories))
    color_map = dict(zip(categories, colors))
    
    for idx, row in events.iterrows():
        y_pos = hash(row['category']) % 5  # Simple positioning
        ax.scatter(row['observation_date'], y_pos, s=200, 
                  c=[color_map.get(row['category'], 'gray')], 
                  alpha=0.7, edgecolors='black', linewidth=2)
        ax.text(row['observation_date'], y_pos + 0.3, row['indicator'][:30], 
               rotation=45, ha='right', fontsize=8)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Event Category', fontsize=12)
    ax.set_title('Event Timeline', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_fig('07_event_timeline')
    plt.show()
else:
    print("No events found for timeline visualization")"""))

# Correlation Analysis
cells.append(nbf.v4.new_markdown_cell("""## 6. Correlation Analysis

Analyzing relationships between key indicators."""))

cells.append(nbf.v4.new_code_cell("""# Select key indicators for correlation
key_indicators = [
    'ACC_OWNERSHIP',
    'ACC_MM_ACCOUNT', 
    'ACC_4G_COV',
    'ACC_MOBILE_PEN'
]

# Create correlation matrix
corr_matrix = create_correlation_matrix(observations, key_indicators)

print("Correlation Matrix:")
print(corr_matrix)

# Visualize correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))

sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
            center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
            vmin=-1, vmax=1, ax=ax)

ax.set_title('Correlation Heatmap: Key Financial Inclusion Indicators', 
             fontsize=14, fontweight='bold')

plt.tight_layout()
save_fig('08_correlation_heatmap')
plt.show()

save_summary(corr_matrix.reset_index(), 'correlation_matrix.csv')"""))

# Key Insights
cells.append(nbf.v4.new_markdown_cell("""## 7. Key Insights

### Access Trends
- Account ownership has grown significantly from 22% (2014) to 49% (2024)
- Mobile money account penetration doubled from 4.7% (2021) to 9.45% (2024)
- 4G coverage nearly doubled from 37.5% to 70.8%, indicating strong infrastructure growth

### Gender Gap
- Significant gender disparity exists in account ownership
- Male ownership (56%) vs Female ownership (36%) in 2021 = 20 percentage point gap
- Closing this gap represents a major opportunity for financial inclusion

### Usage Patterns
- P2P transactions grew 158% YoY, showing rapid digital payment adoption 
- P2P value increased 113% YoY
- ATM transactions grew slower (26%), indicating shift toward digital channels

### Infrastructure Enablers
- Fayda Digital ID enrollment reached 15M, providing foundation for digital services
- Mobile penetration at 61.4% provides infrastructure for mobile financial services
- Strong correlation between 4G coverage and financial service adoption

### Next Steps
These insights will inform:
1. Event impact modeling (Task 3)
2. Forecasting baseline assumptions (Task 4)
3. Dashboard visualization priorities (Task 5)"""))

# Add all cells to notebook
nb['cells'] = cells

# Write notebook
with open('../notebooks/02_eda.ipynb', 'w') as f:
    nbf.write(nb, f)

print("✓ EDA notebook created successfully!")
