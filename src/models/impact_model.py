
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImpactModel:
    """
    Class to model and quantify the impact of key events on financial inclusion indicators.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the ImpactModel with the unified dataset.
        
        Parameters:
        -----------
        df : pd.DataFrame
            The unified dataset containing 'observation_date', 'indicator_code', 'value_numeric', etc.
        """
        self.df = df.copy()
        self.df['observation_date'] = pd.to_datetime(self.df['observation_date'])
        self.events = {}  # Dictionary to store event metadata
        self.impact_estimates = {}

    def add_event(self, event_name: str, event_date: str, description: str = ""):
        """
        Register an event for analysis.
        
        Parameters:
        -----------
        event_name : str
            Unique identifier for the event
        event_date : str
            Date of the event (YYYY-MM-DD)
        description : str
            Optional description
        """
        try:
            self.events[event_name] = {
                'date': pd.to_datetime(event_date),
                'description': description
            }
            logger.info(f"Added event: {event_name} on {event_date}")
        except Exception as e:
            logger.error(f"Failed to add event {event_name}: {e}")

    def get_event_indicator_matrix(self, start_date: str, end_date: str, freq: str = 'M') -> pd.DataFrame:
        """
        Build a binary matrix of coverage for events over time.
        
        Parameters:
        -----------
        start_date : str
            Start of the timeline
        end_date : str
            End of the timeline
        freq : str
            Frequency of the time index (default 'M' for Month)
            
        Returns:
        -----------
        pd.DataFrame
            Matrix with DateTimeIndex and columns for each event (0 = pre-event, 1 = post-event)
        """
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        matrix = pd.DataFrame(index=date_range)
        
        for event_name, meta in self.events.items():
            event_date = meta['date']
            # Create binary step variable: 1 if index >= event_date, else 0
            matrix[event_name] = (matrix.index >= event_date).astype(int)
            
        return matrix

    def run_interrupted_time_series(self, indicator_code: str, event_name: str, 
                                   window_months: int = 24) -> Optional[Dict]:
        """
        Run Interrupted Time Series (ITS) analysis for a specific event and indicator.
        
        Model: Y = β0 + β1*T + β2*D + β3*P + ε
        Where:
            T = Time since start
            D = Dummy for event (0 pre, 1 post)
            P = Time since event (0 pre, values post)
            
        Parameters:
        -----------
        indicator_code : str
            The target indicator to analyze
        event_name : str
            The event to test
        window_months : int
            Number of months before and after event to include in window
            
        Returns:
        -----------
        Dict
            Statistical results summary
        """
        if event_name not in self.events:
            logger.error(f"Event {event_name} not found.")
            return None
            
        event_date = self.events[event_name]['date']
        
        # 1. Prepare Data
        # Filter for indicator
        data = self.df[self.df['indicator_code'] == indicator_code].copy()
        if data.empty:
            logger.warning(f"No data for indicator {indicator_code}")
            return None
            
        # Isolate window around event
        start_monitor = event_date - pd.DateOffset(months=window_months)
        end_monitor = event_date + pd.DateOffset(months=window_months)
        
        mask = (data['observation_date'] >= start_monitor) & (data['observation_date'] <= end_monitor)
        subset = data.loc[mask].copy()
        
        if len(subset) < 10: # Minimum data points check
            logger.warning(f"Not enough data points ({len(subset)}) for ITS analysis on {indicator_code} around {event_name}")
            return None
            
        # Sort by date
        subset = subset.sort_values('observation_date')
        
        # 2. Construct ITS Variables
        # T: Time trend (simple integer sequence)
        subset['T'] = range(len(subset))
        
        # D: Intervention dummy (1 if post-event)
        subset['D'] = (subset['observation_date'] >= event_date).astype(int)
        
        # P: Time after intervention (T - T_event for post-event, 0 for pre-event)
        # Find the index of the first post-event observation
        post_event_start_idx = subset[subset['D'] == 1].index.min()
        
        if pd.isna(post_event_start_idx):
             # No post event data
             logger.warning("No post-event data found in window.")
             return None
             
        # T value at the start of intervention
        # We need the T value corresponding to the first 'D=1' to set the baseline for P
        # However, typically P counts up from 0 starting AT the intervention.
        # Let's align P such that P=0 at the first intervention point.
        
        t_intervention = subset.loc[subset['D'] == 1, 'T'].min()
        subset['P'] = np.where(subset['D'] == 1, subset['T'] - t_intervention, 0)
        
        # 3. Fit OLS Model
        try:
            # Model: value_numeric ~ T + D + P
            mod = smf.ols(formula='value_numeric ~ T + D + P', data=subset)
            res = mod.fit()
            
            # 4. Extract Results
            result = {
                'event': event_name,
                'indicator': indicator_code,
                'baseline_level': res.params['Intercept'],
                'baseline_trend': res.params['T'],
                'immediate_impact': res.params['D'], # Level change
                'trend_change': res.params['P'],     # Slope change
                'p_value_impact': res.pvalues['D'],
                'p_value_trend': res.pvalues['P'],
                'r_squared': res.rsquared,
                'model_summary': res.summary().as_text()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"OLS Regression failed: {e}")
            return None

    def export_results(self, results_list: List[Dict]) -> pd.DataFrame:
        """Convert list of result dicts to DataFrame for easy viewing."""
        return pd.DataFrame(results_list)
