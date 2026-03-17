
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.patches import Patch
from .config import HORIZON_COLORS, HORIZON_AGES

def plot_displacement_profile(ax, df: pd.DataFrame, 
                              show_legend=True, show_xlabel=True, show_ylabel=True, 
                              title=None, x_limits=None, y_limits=None):
    """
    Plots fault displacement vs distance for multiple horizons.
    """
    horizons = df['Horizon'].unique()
    
    # Filter out unwanted horizons
    excluded_horizons = ['Surface', 'Q_Base', 'Quaternary_Base']
    horizons = [h for h in horizons if h not in excluded_horizons]

    # Import MultipleLocator for uniform ticking
    from matplotlib.ticker import MultipleLocator
    
    # Store horizon data for path tracing
    horizon_data_map = {}

    for j, horizon in enumerate(horizons):
        horizon_data = df[df['Horizon'] == horizon].sort_values('Distance')
        
        # Use display name for label
        label = horizon
        
        # Use config color if available
        color = HORIZON_COLORS.get(horizon, None)
        if color is None:
            color = plt.cm.tab10.colors[j % 10]
            
        # Plot line - Convert Distance to km
        x_km = horizon_data['Distance'] / 1000.0
        y_disp = horizon_data['Fault displacement']
        
        ax.plot(
            x_km,
            y_disp,
            linestyle='-',
            color=color,
            linewidth=1.5,
            label=label
        )
        
        # Store for path tracing
        horizon_data_map[horizon] = {'x': x_km.values, 'y': y_disp.values}
        

    if show_xlabel:
        ax.set_xlabel('Distance (km)')
    
    if show_ylabel:
        ax.set_ylabel('Fault throw (m)') 
        
    if title:
        ax.set_title(title, fontweight='bold', fontsize=10)
        
    if x_limits:
        ax.set_xlim(x_limits)
    if y_limits:
        ax.set_ylim(y_limits)
        
    # Uniform Grid and Ticks
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.xaxis.set_major_locator(MultipleLocator(2)) 
    ax.yaxis.set_major_locator(MultipleLocator(100)) 
    
    if show_legend:
        ax.legend(fontsize=8)


def plot_ei_step_chart_generic(ax, fault_data: pd.DataFrame, error_data: pd.DataFrame = None, 
                               value_col='EI', unc_col='EI_Unc', 
                               color_line='blue', x_label='Expansion Index', x_limits=(0.8, 2.0)):
    """
    Generic function to plot EI or Normalized EI step charts.
    """
    if fault_data.empty:
        return

    # Prepare data for plotting (extend to base)
    plot_data = fault_data.copy().sort_values('Age (Ma)')
    
    # Find next age for the last point to close the step
    last_age = plot_data.iloc[-1]['Age (Ma)']
    sorted_ages = sorted(HORIZON_AGES.values())
    next_ages = [a for a in sorted_ages if a > last_age]
    
    if next_ages:
        next_age = next_ages[0]
        new_row = plot_data.iloc[-1].copy()
        new_row['Age (Ma)'] = next_age
        plot_data = pd.concat([plot_data, pd.DataFrame([new_row])], ignore_index=True)

    # Construct vertical step path manually
    step_x = []
    step_y = []
    
    ages = plot_data['Age (Ma)'].values
    vals = plot_data[value_col].values
    
    if len(ages) > 0:
        step_x.append(vals[0])
        step_y.append(ages[0])
        
        for i in range(len(ages) - 1):
            step_x.append(vals[i])
            step_y.append(ages[i+1])
            step_x.append(vals[i+1])
            step_y.append(ages[i+1])

    # Plot the constructed step line
    ax.plot(step_x, step_y, color=color_line, linewidth=2)
    
    # Fill between horizons
    for j in range(len(plot_data) - 1):
        y1, y2 = plot_data.iloc[j]['Age (Ma)'], plot_data.iloc[j + 1]['Age (Ma)']
        val = plot_data.iloc[j][value_col]
        horizon_name = plot_data.iloc[j]['Horizon']
        color = HORIZON_COLORS.get(horizon_name, 'gray')
        baseline = x_limits[0]
        ax.fill_betweenx([y1, y2], baseline, val, color=color, alpha=0.3)

    # Plot error bars if provided
    if error_data is not None and not error_data.empty:
        ax.errorbar(
            error_data[value_col],
            error_data['Mid_Age (Ma)'],
            xerr=error_data[unc_col],
            fmt='none',
            ecolor='salmon', 
            elinewidth=1.5,
            capsize=5,
            alpha=0.8
        )
        
    ax.axvline(x=1.0, color='black', linestyle='--', linewidth=1, alpha=0.7)

    ax.set_xlabel(x_label)
    ax.set_ylabel('Age (Ma)')
    ax.set_ylim(40, 0) 
    ax.set_xlim(x_limits)
    ax.grid(True, linestyle='--', alpha=0.5)
