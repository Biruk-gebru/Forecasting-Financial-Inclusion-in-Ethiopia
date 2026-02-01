"""
Helper utilities for the Ethiopia Financial Inclusion Forecasting project.

This module provides common functions for data processing, visualization,
and report generation across all notebooks.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


# Path configurations
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw')
DATA_PROCESSED_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed')
REPORTDATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'reportdata')
FIGURES_PATH = os.path.join(REPORTDATA_PATH, 'figures')
SUMMARIES_PATH = os.path.join(REPORTDATA_PATH, 'summaries')


def ensure_directories():
    """Ensure all required directories exist."""
    for path in [DATA_PROCESSED_PATH, FIGURES_PATH, SUMMARIES_PATH]:
        os.makedirs(path, exist_ok=True)


def save_figure(fig_name, dpi=300, bbox_inches='tight', verbose=True):
    """
    Save matplotlib figure to reportdata/figures directory.
    
    Parameters:
    -----------
    fig_name : str
        Name of the figure (without extension)
    dpi : int
        Resolution of the saved figure
    bbox_inches : str
        Bounding box adjustment
    verbose : bool
        Print confirmation message
    """
    ensure_directories()
    filepath = os.path.join(FIGURES_PATH, f'{fig_name}.png')
    plt.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
    if verbose:
        print(f"✓ Saved figure: {fig_name}.png")
    return filepath


def save_summary(df, filename, verbose=True):
    """
    Save summary dataframe to reportdata/summaries directory.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame to save
    filename : str
        Name of the file (should include .csv extension)
    verbose : bool
        Print confirmation message
    """
    ensure_directories()
    filepath = os.path.join(SUMMARIES_PATH, filename)
    df.to_csv(filepath, index=False)
    if verbose:
        print(f"✓ Saved summary: {filename}")
    return filepath


def load_unified_data(filepath=None):
    """
    Load the Ethiopia FI unified dataset.
    
    Parameters:
    -----------
    filepath : str, optional
        Custom path to the dataset. If None, uses default location.
    
    Returns:
    --------
    pd.DataFrame
        Loaded dataset
    """
    if filepath is None:
        filepath = os.path.join(DATA_RAW_PATH, 'ethiopia_fi_unified_data.csv')
    
    df = pd.read_csv(filepath)
    
    # Parse dates
    date_columns = ['observation_date', 'event_date', 'target_year']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df


def get_observations(df):
    """Extract observation records from unified dataset."""
    return df[df['record_type'] == 'observation'].copy()


def get_events(df):
    """Extract event records from unified dataset."""
    return df[df['record_type'] == 'event'].copy()


def get_impact_links(df):
    """Extract impact_link records from unified dataset."""
    return df[df['record_type'] == 'impact_link'].copy()


def get_targets(df):
    """Extract target records from unified dataset."""
    return df[df['record_type'] == 'target'].copy()


def setup_plot_style():
    """Configure default plot styling."""
    sns.set_style('whitegrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12


def create_exploration_summary(df):
    """
    Create a comprehensive summary of the dataset for reporting.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Unified dataset
    
    Returns:
    --------
    dict
        Dictionary containing summary statistics
    """
    observations = get_observations(df)
    events = get_events(df)
    impact_links = get_impact_links(df)
    targets = get_targets(df)
    
    summary = {
        'total_records': len(df),
        'observations': len(observations),
        'events': len(events),
        'impact_links': len(impact_links),
        'targets': len(targets),
        'unique_indicators': observations['indicator_code'].nunique() if len(observations) > 0 else 0,
        'temporal_start': observations['observation_date'].min() if len(observations) > 0 else None,
        'temporal_end': observations['observation_date'].max() if len(observations) > 0 else None,
        'high_confidence_pct': (observations['confidence'] == 'high').sum() / len(observations) * 100 if len(observations) > 0 else 0
    }
    
    return summary


def print_section_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")
