"""
Utility functions for Ethiopia Financial Inclusion Analysis
"""

import pandas as pd
import numpy as np
import os


def save_fig(fig_name, path='../data/reportdata/figures', dpi=300, bbox_inches='tight'):
    """Save figure to reportdata/figures directory"""
    filepath = os.path.join(path, f'{fig_name}.png')
    import matplotlib.pyplot as plt
    plt.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
    print(f"✓ Saved: {fig_name}.png")


def save_summary(df, filename, path='../data/reportdata/summaries'):
    """Save summary dataframe to reportdata/summaries directory"""
    filepath = os.path.join(path, filename)
    df.to_csv(filepath, index=False)
    print(f"✓ Saved: {filename}")


def calculate_growth_rate(df, indicator_code, date_col='observation_date'):
    """
    Calculate year-over-year growth rates for an indicator
    
    Parameters:
    -----------
    df : DataFrame
        Data containing the indicator
    indicator_code : str
        The indicator code to calculate growth for
    date_col : str
        Name of the date column
        
    Returns:
    --------
    DataFrame with year, value, and growth_rate columns
    """
    # Filter for specific indicator
    indicator_df = df[df['indicator_code'] == indicator_code].copy()
    indicator_df[date_col] = pd.to_datetime(indicator_df[date_col])
    indicator_df['year'] = indicator_df[date_col].dt.year
    
    # Group by year and get mean value
    yearly = indicator_df.groupby('year')['value_numeric'].mean().reset_index()
    yearly = yearly.sort_values('year')
    
    # Calculate growth rate
    yearly['growth_rate'] = yearly['value_numeric'].pct_change() * 100
    
    return yearly


def calculate_gender_gap(df, indicator_code, date_col='observation_date'):
    """
    Calculate gender gap for an indicator
    
    Parameters:
    -----------
    df : DataFrame
        Data containing the indicator with gender breakdown
    indicator_code : str
        The indicator code to analyze
    date_col : str
        Name of the date column
        
    Returns:
    --------
    DataFrame with year, male, female, and gap columns
    """
    # Filter for specific indicator
    indicator_df = df[df['indicator_code'] == indicator_code].copy()
    indicator_df[date_col] = pd.to_datetime(indicator_df[date_col])
    indicator_df['year'] = indicator_df[date_col].dt.year
    
    # Pivot to get male and female values
    gender_pivot = indicator_df.pivot_table(
        values='value_numeric',
        index='year',
        columns='gender',
        aggfunc='mean'
    ).reset_index()
    
    # Calculate gap
    if 'male' in gender_pivot.columns and 'female' in gender_pivot.columns:
        gender_pivot['gap'] = gender_pivot['male'] - gender_pivot['female']
        gender_pivot['gap_pct'] = (gender_pivot['gap'] / gender_pivot['female']) * 100
    
    return gender_pivot


def create_correlation_matrix(df, indicators):
    """
    Create correlation matrix for selected indicators
    
    Parameters:
    -----------
    df : DataFrame
        Full dataset
    indicators : list
        List of indicator codes to include
        
    Returns:
    --------
    Correlation matrix DataFrame
    """
    # Pivot data to wide format
    pivot_df = df[df['indicator_code'].isin(indicators)].pivot_table(
        values='value_numeric',
        index='observation_date',
        columns='indicator_code',
        aggfunc='mean'
    )
    
    # Calculate correlation
    corr_matrix = pivot_df.corr()
    
    return corr_matrix
