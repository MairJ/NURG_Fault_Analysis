
import pandas as pd
import numpy as np
from .config import HORIZON_AGES

def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Expansion Index (EI), Differential Movement (D_m), and other metrics.
    """
    df = df.copy()
    
    # Sort by Fault and Age
    df = df.sort_values(by=['Fault', 'Age (Ma)']).reset_index(drop=True)
    
    # Calculate EI
    if 'T_down (m)' in df.columns and 'T_up (m)' in df.columns:
        df['EI'] = df['T_down (m)'] / df['T_up (m)']
        
        # Uncertainty for EI (assuming 5m uncertainty on T_up and T_down)
        # EI_unc = EI * sqrt( (dT/T_down)^2 + (dT/T_up)^2 )
        df['EI_Unc'] = df['EI'] * np.sqrt( (5 / df['T_down (m)'].abs().clip(lower=5))**2 + 
                                           (5 / df['T_up (m)'].abs().clip(lower=5))**2 )
    
    # Calculate D_m
    # D_m = Fault displacement / Delta_t
    # First ensure we have Delta_t or calculate it
    if 'Delta_t (Ma)' not in df.columns:
         df['Delta_Age (Ma)'] = df.groupby('Fault')['Age (Ma)'].diff()
         # Use calculated delta age if original delta_t is missing or 0
         df['Delta_t (Ma)'] = df['Delta_Age (Ma)']

    if 'Fault displacement' in df.columns:
         df['D_m'] = np.where(
            (df['Delta_t (Ma)'].notnull()) & (df['Delta_t (Ma)'] != 0),
            df['Fault displacement'] / df['Delta_t (Ma)'],
            np.nan
        )

    # Calculate FAI (Fault Activity Index) = Displacement / Age
    if 'Fault displacement' in df.columns and 'Age (Ma)' in df.columns:
         df['FAI'] = df['Fault displacement'] / df['Age (Ma)'].replace(0, np.nan)

    return df

def prepare_step_plot_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares data for step plotting (calculating mid-points for error bars).
    """
    mid_ages_list = []
    ei_values_list = []
    ei_unc_list = []
    faults_list = []
    
    for fault in df['Fault'].unique():
        fault_data = df[df['Fault'] == fault].sort_values('Age (Ma)').reset_index()
        for i in range(1, len(fault_data)):
            current_age = fault_data.loc[i, 'Age (Ma)']
            previous_age = fault_data.loc[i - 1, 'Age (Ma)']
            mid_age = (current_age + previous_age) / 2
            
            # Use the value from the interval (i-1)
            if 'EI' in fault_data.columns:
                ei_value = fault_data.loc[i - 1, 'EI']
                ei_unc = fault_data.loc[i - 1, 'EI_Unc'] if 'EI_Unc' in fault_data.columns else 0
                
                mid_ages_list.append(mid_age)
                ei_values_list.append(ei_value)
                ei_unc_list.append(ei_unc)
                faults_list.append(fault)

        # Handle the last interval (from last horizon to next horizon/base)
        if not fault_data.empty:
            last_idx = len(fault_data) - 1
            last_age = fault_data.loc[last_idx, 'Age (Ma)']
            last_horizon = fault_data.loc[last_idx, 'Horizon']
            
            # Find next age
            sorted_ages = sorted(HORIZON_AGES.values())
            # Find the age immediately greater than last_age
            next_ages = [a for a in sorted_ages if a > last_age]
            
            if next_ages:
                next_age = next_ages[0]
                mid_age = (last_age + next_age) / 2
                
                if 'EI' in fault_data.columns:
                    ei_value = fault_data.loc[last_idx, 'EI']
                    ei_unc = fault_data.loc[last_idx, 'EI_Unc'] if 'EI_Unc' in fault_data.columns else 0
                    
                    mid_ages_list.append(mid_age)
                    ei_values_list.append(ei_value)
                    ei_unc_list.append(ei_unc)
                    faults_list.append(fault)
                
    return pd.DataFrame({
        'Fault': faults_list,
        'Mid_Age (Ma)': mid_ages_list,
        'EI': ei_values_list,
        'EI_Unc': ei_unc_list
    })

def calculate_normalized_ei(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Normalized EI (EI / Max(EI) per fault).
    """
    df = df.copy()
    
    # Calculate Max EI per fault
    max_ei = df.groupby('Fault')['EI'].transform('max')
    
    df['EI_Normalized'] = df['EI'] / max_ei
    
    # Propagate uncertainty: Norm_Unc = EI_Unc / Max_EI 
    # (Simplified assumption: Max_EI has negligible error relative to individual points, 
    # or we just scale the error bar)
    if 'EI_Unc' in df.columns:
        df['EI_Normalized_Unc'] = df['EI_Unc'] / max_ei
        
    return df

def prepare_normalized_step_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares error bar data for Normalized EI.
    """
    # Reuse the logic but for normalized columns
    mid_ages_list = []
    norm_values_list = []
    norm_unc_list = []
    faults_list = []
    
    for fault in df['Fault'].unique():
        fault_data = df[df['Fault'] == fault].sort_values('Age (Ma)').reset_index()
        for i in range(1, len(fault_data)):
            current_age = fault_data.loc[i, 'Age (Ma)']
            previous_age = fault_data.loc[i - 1, 'Age (Ma)']
            mid_age = (current_age + previous_age) / 2
            
            if 'EI_Normalized' in fault_data.columns:
                val = fault_data.loc[i - 1, 'EI_Normalized']
                unc = fault_data.loc[i - 1, 'EI_Normalized_Unc'] if 'EI_Normalized_Unc' in fault_data.columns else 0
                
                mid_ages_list.append(mid_age)
                norm_values_list.append(val)
                norm_unc_list.append(unc)
                faults_list.append(fault)

        # Handle the last interval
        if not fault_data.empty:
            last_idx = len(fault_data) - 1
            last_age = fault_data.loc[last_idx, 'Age (Ma)']
            
            sorted_ages = sorted(HORIZON_AGES.values())
            next_ages = [a for a in sorted_ages if a > last_age]
            
            if next_ages:
                next_age = next_ages[0]
                mid_age = (last_age + next_age) / 2
                
                if 'EI_Normalized' in fault_data.columns:
                    val = fault_data.loc[last_idx, 'EI_Normalized']
                    unc = fault_data.loc[last_idx, 'EI_Normalized_Unc'] if 'EI_Normalized_Unc' in fault_data.columns else 0
                    
                    mid_ages_list.append(mid_age)
                    norm_values_list.append(val)
                    norm_unc_list.append(unc)
                    faults_list.append(fault)
                
    return pd.DataFrame({
        'Fault': faults_list,
        'Mid_Age (Ma)': mid_ages_list,
        'EI_Normalized': norm_values_list,
        'EI_Normalized_Unc': norm_unc_list
    })

def remove_outliers(df: pd.DataFrame, column: str = 'Fault displacement', window: int = 5, threshold: float = 100.0) -> pd.DataFrame:
    """
    Removes outliers from a dataframe column using a rolling median filter.
    Preserves original index but returns a copy with outliers removed (rows dropped).
    """
    df_clean = df.copy()
    
    # Calculate rolling median
    rolling_median = df_clean[column].rolling(window=window, center=True).median()
    
    # Fill NaN at edges with original values (or nearest) - simpler to just ignore edges for filtering or fill with original
    rolling_median = rolling_median.fillna(df_clean[column])
    
    # Calculate difference
    diff = abs(df_clean[column] - rolling_median)
    
    # Filter
    mask = diff <= threshold
    
    # Check what is being removed
    removed = df_clean[~mask]
    if not removed.empty:
        print(f"DEBUG: Removing {len(removed)} outliers from {column}.")
        
    return df_clean[mask]
