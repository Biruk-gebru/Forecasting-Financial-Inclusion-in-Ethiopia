"""
Utility functions for Ethiopia Financial Inclusion Analysis
"""

import pandas as pd
import numpy as np
import os
import logging
from typing import List, Optional, Union
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_fig(fig_name: str, path: str = '../data/reportdata/figures', dpi: int = 300, bbox_inches: str = 'tight') -> None:
    """
    Save figure to reportdata/figures directory with error handling.

    Parameters:
    -----------
    fig_name : str
        Name of the figure file (without extension)
    path : str
        Directory path to save to
    dpi : int
        Dots per inch for resolution
    bbox_inches : str
        Bounding box setting
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created directory: {path}")
            
        filepath = os.path.join(path, f'{fig_name}.png')
        plt.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
        logger.info(f"✓ Saved figure: {fig_name}.png")
    except Exception as e:
        logger.error(f"Failed to save figure {fig_name}: {e}")
        raise

def save_summary(df: pd.DataFrame, filename: str, path: str = '../data/reportdata/summaries') -> None:
    """
    Save summary dataframe to reportdata/summaries directory with validation.

    Parameters:
    -----------
    df : pd.DataFrame
        Data to save
    filename : str
        Name of the CSV file
    path : str
        Directory path to save to
    """
    if df is None or df.empty:
        logger.warning(f"DataFrame for {filename} is empty or None. Skipping save.")
        return

    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created directory: {path}")

        filepath = os.path.join(path, filename)
        df.to_csv(filepath, index=False)
        logger.info(f"✓ Saved summary: {filename}")
    except Exception as e:
        logger.error(f"Failed to save summary {filename}: {e}")
        raise

def calculate_growth_rate(df: pd.DataFrame, indicator_code: str, date_col: str = 'observation_date') -> pd.DataFrame:
    """
    Calculate year-over-year growth rates for an indicator.

    Parameters:
    -----------
    df : pd.DataFrame
        Data containing the indicator
    indicator_code : str
        The indicator code to calculate growth for
    date_col : str
        Name of the date column
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with year, value, and growth_rate columns
    """
    required_cols = ['indicator_code', 'value_numeric', date_col]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns in DataFrame: {missing}")

    # Filter for specific indicator
    indicator_df = df[df['indicator_code'] == indicator_code].copy()
    
    if indicator_df.empty:
        logger.warning(f"No data found for indicator: {indicator_code}")
        return pd.DataFrame(columns=['year', 'value_numeric', 'growth_rate'])

    try:
        indicator_df[date_col] = pd.to_datetime(indicator_df[date_col])
        indicator_df['year'] = indicator_df[date_col].dt.year
        
        # Group by year and get mean value (handling duplicates)
        yearly = indicator_df.groupby('year')['value_numeric'].mean().reset_index()
        yearly = yearly.sort_values('year')
        
        # Calculate growth rate
        yearly['growth_rate'] = yearly['value_numeric'].pct_change() * 100
        
        return yearly
    except Exception as e:
        logger.error(f"Error calculating growth rate for {indicator_code}: {e}")
        return pd.DataFrame()

def calculate_gender_gap(df: pd.DataFrame, indicator_code: str, date_col: str = 'observation_date') -> pd.DataFrame:
    """
    Calculate gender gap for an indicator.

    Parameters:
    -----------
    df : pd.DataFrame
        Data containing the indicator with gender breakdown
    indicator_code : str
        The indicator code to analyze
    date_col : str
        Name of the date column
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with year, male, female, and gap columns
    """
    required_cols = ['indicator_code', 'value_numeric', 'gender', date_col]
    if not all(col in df.columns for col in required_cols):
         missing = [col for col in required_cols if col not in df.columns]
         raise ValueError(f"Missing required columns: {missing}")

    # Filter for specific indicator
    indicator_df = df[df['indicator_code'] == indicator_code].copy()
    
    if indicator_df.empty:
        logger.warning(f"No data found for indicator: {indicator_code}")
        return pd.DataFrame()

    try:
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
            if 'gap_pct' in gender_pivot.columns:
                 # Clean infinite values if female rate is 0
                gender_pivot['gap_pct'] = gender_pivot['gap_pct'].replace([np.inf, -np.inf], np.nan)

        return gender_pivot
    except Exception as e:
        logger.error(f"Error calculating gender gap for {indicator_code}: {e}")
        return pd.DataFrame()

def create_correlation_matrix(df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
    """
    Create correlation matrix for selected indicators.

    Parameters:
    -----------
    df : pd.DataFrame
        Full dataset
    indicators : list
        List of indicator codes to include
        
    Returns:
    --------
    pd.DataFrame
        Correlation matrix DataFrame
    """
    if df.empty:
         logger.warning("Empty DataFrame provided for correlation matrix.")
         return pd.DataFrame()

    # Filter data first
    subset_df = df[df['indicator_code'].isin(indicators)]
    
    if subset_df.empty:
        logger.warning(f"No data found for specified indicators: {indicators}")
        return pd.DataFrame()

    try:
        # Pivot data to wide format
        pivot_df = subset_df.pivot_table(
            values='value_numeric',
            index='observation_date',
            columns='indicator_code',
            aggfunc='mean'
        )
        
        if pivot_df.empty:
             logger.warning("Pivot resulted in empty DataFrame (no overlapping dates?).")
             return pd.DataFrame()

        # Calculate correlation
        corr_matrix = pivot_df.corr()
        
        return corr_matrix
    except Exception as e:
        logger.error(f"Error creating correlation matrix: {e}")
        return pd.DataFrame()

def calculate_forecast(df: pd.DataFrame, indicator_code: str, years_ahead: int = 5, date_col: str = 'observation_date') -> pd.DataFrame:
    """
    Calculate forecast for an indicator using linear regression.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Data containing the indicator
    indicator_code : str
        The indicator code to forecast
    years_ahead : int
        Number of years to forecast
    date_col : str
        Name of the date column
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with year, value, type (historical/forecast), and confidence intervals
    """
    try:
        from sklearn.linear_model import LinearRegression
        import scipy.stats as stats
    except ImportError:
        logger.error("scikit-learn or scipy not installed. Cannot perform forecasting.")
        return pd.DataFrame()

    # Filter for specific indicator
    indicator_df = df[df['indicator_code'] == indicator_code].copy()
    
    if indicator_df.empty:
        logger.warning(f"No data found for indicator: {indicator_code}")
        return pd.DataFrame()
        
    try:
        # Prepare data
        indicator_df[date_col] = pd.to_datetime(indicator_df[date_col])
        indicator_df['year'] = indicator_df[date_col].dt.year
        
        # Aggregation by year (mean) to handle multiple observations per year
        yearly_data = indicator_df.groupby('year')['value_numeric'].mean().reset_index()
        
        if len(yearly_data) < 2:
            logger.warning(f"Not enough data points to forecast {indicator_code}")
            return pd.DataFrame()

        X = yearly_data['year'].values.reshape(-1, 1)
        y = yearly_data['value_numeric'].values
        
        # Fit model
        model = LinearRegression()
        model.fit(X, y)
        
        # Future years
        last_year = yearly_data['year'].max()
        future_years = np.array(range(last_year + 1, last_year + years_ahead + 1)).reshape(-1, 1)
        
        all_years = np.vstack((X, future_years))
        
        # Predict
        predictions = model.predict(all_years)
        
        # Calculate Confidence Intervals
        # 1. Standard Error of Estimate
        y_pred_hist = model.predict(X)
        residuals = y - y_pred_hist
        sum_squared_residuals = np.sum(residuals ** 2)
        dof = len(y) - 2
        mse = sum_squared_residuals / dof
        se_est = np.sqrt(mse)
        
        # 2. Prediction Interval for each point
        mean_x = np.mean(X)
        n = len(X)
        sum_sq_diff_x = np.sum((X - mean_x) ** 2)
        
        t_stat = stats.t.ppf(0.975, dof) # 95% confidence
        
        conf_intervals = []
        for x_val in all_years.flatten():
            se_pred = se_est * np.sqrt(1 + 1/n + (x_val - mean_x)**2 / sum_sq_diff_x)
            margin = t_stat * se_pred
            conf_intervals.append(margin)
            
        conf_intervals = np.array(conf_intervals)
        
        # Construct Result DataFrame
        result_df = pd.DataFrame({
            'year': all_years.flatten(),
            'value': predictions,
            'lower_ci': predictions - conf_intervals,
            'upper_ci': predictions + conf_intervals,
            'type': ['Historical' if y <= last_year else 'Forecast' for y in all_years.flatten()]
        })
        
        # Overlay actual historical values where available
        result_df = result_df.merge(yearly_data, on='year', how='left')
        result_df['final_value'] = result_df['value_numeric'].combine_first(result_df['value'])
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error calculating forecast for {indicator_code}: {e}")
        return pd.DataFrame()
