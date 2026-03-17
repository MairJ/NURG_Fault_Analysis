
import pandas as pd
import os
from typing import List, Dict, Optional

def load_fault_excel_files(file_paths: List[str], base_dir: str = '.') -> List[pd.DataFrame]:
    """
    Loads a list of Excel files containing fault data.
    """
    dataframes = []
    for file_path in file_paths:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            df = pd.read_excel(full_path)
            # Add a column for the source file name (without extension)
            df['Source_File'] = os.path.splitext(os.path.basename(file_path))[0]
            dataframes.append(df)
        else:
            print(f"Warning: File not found: {full_path}")
    return dataframes

def load_combined_csv(file_path: str) -> pd.DataFrame:
    """
    Loads the combined CSV file and performs initial cleaning.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Combined data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Ensure numeric columns
    numeric_cols = ['Age (Ma)', 'Delta_t (Ma)', 'T_up (m)', 'T_down (m)', 'Throw (m)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Calculate Fault displacement if missing but T_down and T_up exist
    if 'Fault displacement' not in df.columns:
        if 'T_down (m)' in df.columns and 'T_up (m)' in df.columns:
             df['Fault displacement'] = df['T_down (m)'] - df['T_up (m)']
        elif 'Throw (m)' in df.columns:
             df.rename(columns={'Throw (m)': 'Fault displacement'}, inplace=True)

    return df
