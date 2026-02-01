# Ethiopia Financial Inclusion Forecasting

Forecasting system for Ethiopia's digital financial transformation using time series methods.

## Project Structure
- `data/`: Data directory (ignored by git).
    - `raw/`: Raw input files (e.g., `ethiopia_fi_unified_data.csv`).
    - `processed/`: Cleaned and transformed data.
    - `enriched/`: Data enriched with additional features/events.
    - `reportdata/`: Generated figures and summary tables.
- `notebooks/`: Jupyter notebooks for analysis and modeling.
    - `01_data_exploration.ipynb`: Initial data profiling.
    - `02_eda.ipynb`: Comprehensive exploratory data analysis.
- `src/`: Source code modules.
    - `utils.py`: Helper functions for analysis and visualization.
- `scripts/`: Utility scripts (e.g., notebook generators).
- `dashboard/`: Streamlit dashboard application.
- `reports/`: Final reports and figures.

## Data Schema
The unified dataset (`ethiopia_fi_unified_data.csv`) contains the following key columns:
- `record_id`: Unique identifier.
- `record_type`: Type of record (`observation`, `event`, `target`, etc.).
- `indicator`: Name of the financial inclusion indicator.
- `indicator_code`: Unique code (e.g., `ACC_OWNERSHIP`).
- `value_numeric`: Numeric value of the observation.
- `observation_date`: Date of the observation.
- `category`: Category for events (e.g., `policy`, `product_launch`).
- `gender`: Gender disaggregation (`all`, `male`, `female`).

## Usage

### Setup
1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd ethiopia-financial-inclusion
   ```
2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running Analysis
- Run the EDA analysis:
  ```bash
  jupyter notebook notebooks/02_eda.ipynb
  ```
- Generate the EDA notebook from script (reproducibility):
  ```bash
  python scripts/generate_eda_notebook.py
  ```

### Dashboard
- Run the Streamlit dashboard:
  ```bash
  streamlit run dashboard/app.py
  ```
