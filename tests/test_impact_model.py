
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.impact_model import ImpactModel

@pytest.fixture
def sample_data():
    """Create a synthetic dataset for testing."""
    dates = pd.date_range(start='2020-01-01', periods=36, freq='M')
    
    # Create two indicators
    # Ind 1: Step change after 2021-06-01
    values1 = np.concatenate([
        np.random.normal(10, 1, 17), # 2020-01 to 2021-05
        np.random.normal(20, 1, 19)  # 2021-06 to 2022-12
    ])
    
    # Ind 2: Random noise
    values2 = np.random.normal(50, 5, 36)
    
    df1 = pd.DataFrame({
        'observation_date': dates,
        'indicator_code': 'IND_TEST_1',
        'value_numeric': values1
    })
    
    df2 = pd.DataFrame({
        'observation_date': dates,
        'indicator_code': 'IND_TEST_2',
        'value_numeric': values2
    })
    
    return pd.concat([df1, df2], ignore_index=True)

def test_initialization(sample_data):
    model = ImpactModel(sample_data)
    assert not model.df.empty
    assert 'observation_date' in model.df.columns
    assert isinstance(model.df['observation_date'].dtype, object) or np.issubdtype(model.df['observation_date'].dtype, np.datetime64)

def test_add_event(sample_data):
    model = ImpactModel(sample_data)
    model.add_event('Test Event', '2021-06-01', 'Description')
    assert 'Test Event' in model.events
    assert model.events['Test Event']['date'] == pd.Timestamp('2021-06-01')

def test_event_indicator_matrix(sample_data):
    model = ImpactModel(sample_data)
    model.add_event('Event A', '2021-01-01')
    model.add_event('Event B', '2022-01-01')
    
    matrix = model.get_event_indicator_matrix('2020-01-01', '2022-12-31', freq='M')
    
    assert not matrix.empty
    assert 'Event A' in matrix.columns
    assert 'Event B' in matrix.columns
    
    # Check values
    # Event A should be 0 before Jan 2021, 1 after
    assert matrix.loc['2020-12-31', 'Event A'] == 0
    assert matrix.loc['2021-01-31', 'Event A'] == 1
    
    # Event B should be 0 before Jan 2022
    assert matrix.loc['2021-12-31', 'Event B'] == 0
    assert matrix.loc['2022-01-31', 'Event B'] == 1

def test_its_analysis_execution(sample_data):
    model = ImpactModel(sample_data)
    model.add_event('Intervention', '2021-06-01') # Index 17 in the monthly data (0-based)
    
    # IND_TEST_1 has a clear step change, should be significant
    result = model.run_interrupted_time_series('IND_TEST_1', 'Intervention', window_months=12)
    
    assert result is not None
    assert result['event'] == 'Intervention'
    assert result['indicator'] == 'IND_TEST_1'
    # We expect a significant immediate impact (level change) approx +10
    # Allow some noise margin
    assert 8.0 < result['immediate_impact'] < 12.0
    assert result['p_value_impact'] < 0.05

def test_its_insufficient_data(sample_data):
    model = ImpactModel(sample_data)
    model.add_event('Early Event', '2020-02-01')
    
    # Very small window resulting in few points
    result = model.run_interrupted_time_series('IND_TEST_1', 'Early Event', window_months=1)
    # Should ideally warn and return None logic depends on implementation
    # With window=1, we have -1 month, 0, +1 month = 3 points? Implementation detail.
    # Our impl checks len(subset) < 10
    assert result is None

def test_its_unknown_event(sample_data):
    model = ImpactModel(sample_data)
    result = model.run_interrupted_time_series('IND_TEST_1', 'NonExistentEvent')
    assert result is None
