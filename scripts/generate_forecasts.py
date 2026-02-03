
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils import calculate_forecast, save_fig, save_summary, logger

def main():
    logger.info("Starting Task 4: Forecasting Access and Usage...")
    
    # Load data
    # Resolve path relative to script location to be robust
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, '../data/raw/ethiopia_fi_unified_data.csv')
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return
        
    df = pd.read_csv(data_path)
    
    # Indicators to forecast
    indicators = [
        'ACC_OWNERSHIP',      # Account Ownership
        'ACC_MM_ACCOUNT',     # Mobile Money Account
        'USG_P2P_VALUE',      # P2P Transaction Value
        'ACC_MOBILE_PEN'      # Mobile Penetration
    ]
    
    all_forecasts = []
    
    # 1. Baseline Forecasts (Linear Trend)
    logger.info("Generating Baseline Forecasts...")
    for ind in indicators:
        logger.info(f"Forecasting {ind}...")
        forecast_df = calculate_forecast(df, ind, years_ahead=5)
        
        if not forecast_df.empty:
            forecast_df['indicator'] = ind
            forecast_df['scenario'] = 'Baseline'
            all_forecasts.append(forecast_df)
            
            # Plotting
            plt.figure(figsize=(10, 6))
            
            # Historical
            hist = forecast_df[forecast_df['type'] == 'Historical']
            plt.plot(hist['year'], hist['final_value'], 'bo-', label='Historical')
            
            # Forecast
            pred = forecast_df[forecast_df['type'] == 'Forecast']
            plt.plot(pred['year'], pred['final_value'], 'r--', label='Baseline Forecast')
            
            # Confidence Interval
            plt.fill_between(forecast_df['year'], forecast_df['lower_ci'], forecast_df['upper_ci'], 
                             color='gray', alpha=0.2, label='95% Confidence Interval')
            
            plt.title(f'Forecast: {ind} (Baseline)')
            plt.xlabel('Year')
            plt.ylabel('Value')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            save_fig(f'forecast_baseline_{ind}', path='data/reportdata/figures')
            plt.close()

    # 2. Scenario Forecasts (Simple Multipliers on Growth)
    # This is a simplified approach: we take the baseline forecast slope and adjust it.
    # Since our calculate_forecast returns fixed values, we will manually adjust the 'Forecast' portion of the dataframe.
    
    logger.info("Generating Scenario Forecasts...")
    # We will iterate through the baseline forecasts we just created and apply adjustments
    baseline_results = pd.concat(all_forecasts) if all_forecasts else pd.DataFrame()
    
    if not baseline_results.empty:
        scenarios = [
            {'name': 'Optimistic', 'multiplier': 1.15}, # 15% faster growth
            {'name': 'Pessimistic', 'multiplier': 0.85} # 15% slower growth
        ]
        
        for scenario in scenarios:
            scenario_df = baseline_results.copy()
            scenario_df['scenario'] = scenario['name']
            
            # We need to adjust the projected growth relative to the last historical point
            # Identify the last historical year for each indicator
            last_hist_map = scenario_df[scenario_df['type'] == 'Historical'].groupby('indicator')['year'].max().to_dict()
            last_val_map = scenario_df[scenario_df['type'] == 'Historical'].groupby('indicator')['final_value'].last().to_dict() # Assuming sorted
            
            # Apply multiplier to the *change* from the last historical point
            # value_scenario = last_hist_val + (value_baseline - last_hist_val) * multiplier
            
            def adjust_value(row):
                if row['type'] == 'Historical':
                    return row['final_value']
                
                ind = row['indicator']
                last_year = last_hist_map.get(ind)
                last_val = last_val_map.get(ind)
                
                if row['year'] > last_year:
                    baseline_change = row['final_value'] - last_val
                    return last_val + (baseline_change * scenario['multiplier'])
                return row['final_value']

            scenario_df['final_value'] = scenario_df.apply(adjust_value, axis=1)
            # Re-calculate CIs roughly (scaling width) or just leave as is? 
            # For simplicity, we'll shift the CI center but keep the width relative to the new mean.
            ci_width = (scenario_df['upper_ci'] - scenario_df['lower_ci']) / 2
            scenario_df['lower_ci'] = scenario_df['final_value'] - ci_width
            scenario_df['upper_ci'] = scenario_df['final_value'] + ci_width
            
            all_forecasts.append(scenario_df)
            
            # Plotting (Overlaying scenarios for specific indicators)
            # We'll plot all scenarios together later, but let's save individual scenario plots? 
            # Better to save a Combined plot.

    # 3. Combined Visualization (Baseline + Scenarios)
    full_forecast_df = pd.concat(all_forecasts)
    
    for ind in indicators:
        ind_data = full_forecast_df[full_forecast_df['indicator'] == ind]
        if ind_data.empty: continue
        
        plt.figure(figsize=(12, 7))
        
        # Plot Historical (just once)
        hist = ind_data[(ind_data['scenario'] == 'Baseline') & (ind_data['type'] == 'Historical')]
        plt.plot(hist['year'], hist['final_value'], 'ko-', linewidth=2, label='Historical')
        
        # Plot Scenarios
        colors = {'Baseline': 'blue', 'Optimistic': 'green', 'Pessimistic': 'red'}
        styles = {'Baseline': '--', 'Optimistic': '-.', 'Pessimistic': ':'}
        
        for scen_name in ['Baseline', 'Optimistic', 'Pessimistic']:
            scen_data = ind_data[(ind_data['scenario'] == scen_name) & (ind_data['type'] == 'Forecast')]
            if scen_data.empty: continue
            
            plt.plot(scen_data['year'], scen_data['final_value'], 
                     color=colors.get(scen_name, 'gray'), 
                     linestyle=styles.get(scen_name, '-'),
                     label=f'{scen_name} Forecast')
            
            # Plot CI only for Baseline to avoid clutter
            if scen_name == 'Baseline':
                baseline_full = ind_data[ind_data['scenario'] == 'Baseline']
                # Mask historical part for CI to only show forecast uncertainty
                baseline_forecast = baseline_full[baseline_full['type'] == 'Forecast']
                plt.fill_between(baseline_forecast['year'], 
                                 baseline_forecast['lower_ci'], 
                                 baseline_forecast['upper_ci'], 
                                 color='blue', alpha=0.1, label='Baseline 95% CI')

        plt.title(f'Forecast Scenarios: {ind}')
        plt.xlabel('Year')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        save_fig(f'forecast_scenarios_{ind}', path='data/reportdata/figures')
        plt.close()

    # Save summary CSV
    save_summary(full_forecast_df, 'forecast_results.csv', path='data/reportdata/summaries')
    logger.info("Task 4 Forecasting Completed.")

if __name__ == "__main__":
    main()
