import os
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from fai_analysis import config, loader, processing, visualization

def main():
    print("Starting FAI Analysis...")
    
    # Setup Output Directory
    output_dir = 'analysis_output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine local directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Fault Displacement Analysis
    print("Loading Fault Data...")
    fault_dfs = loader.load_fault_excel_files(config.DEFAULT_FAULT_FILES, base_dir=os.path.join(base_dir, config.DATA_DIR))
    
    # Pre-process DataFrames
    sorted_dfs = []
    for df in fault_dfs:
        if 'Distance' in df.columns:
            df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
        if 'Fault displacement' in df.columns:
            df['Fault displacement'] = pd.to_numeric(df['Fault displacement'], errors='coerce')
        if 'Horizon' in df.columns and 'Distance' in df.columns:
            df = df.sort_values(by=['Horizon', 'Distance'])
        sorted_dfs.append(df)
    fault_dfs = sorted_dfs

    # 2. EI and Metrics Analysis
    print("Loading Combined Data...")
    try:
        combined_path = os.path.join(base_dir, config.DATA_DIR, config.COMBINED_DATA_FILE)
        combined_df = loader.load_combined_csv(combined_path)
    except FileNotFoundError:
        print(f"Error: {config.COMBINED_DATA_FILE} not found.")
        combined_df = pd.DataFrame()

    if not combined_df.empty and 'Fault' in combined_df.columns:
        print("Calculating Metrics...")
        combined_df = processing.calculate_metrics(combined_df)
        combined_df = processing.calculate_normalized_ei(combined_df)
        
        error_data = processing.prepare_step_plot_data(combined_df)
        norm_error_data = processing.prepare_normalized_step_data(combined_df)

        # Generate EI Comparison Figure
        print("Generating EI Comparison Figure...")
        fault_order = ['1A', '1B', '1C', '1D', '1E', '2A', '2B']
        ncols = 4
        nrows = (len(fault_order) + ncols - 1) // ncols
        total_plot_rows = 2 * nrows
        
        fig_width = config.FIGURE_WIDTH_2COL_INCH
        fig_height = (22 / 2.54) * (total_plot_rows / 4) 
        
        plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 10})
        fig = plt.figure(figsize=(fig_width, fig_height))
        
        # Absolute EI Plots
        for i, fault in enumerate(fault_order):
            ax = fig.add_subplot(total_plot_rows, ncols, (i // ncols * ncols) + i % ncols + 1)
            f_data = combined_df[combined_df['Fault'] == fault]
            f_err = error_data[error_data['Fault'] == fault]
            is_bottom = ((i // ncols + 1) * ncols + i % ncols) >= len(fault_order)
            
            visualization.plot_ei_step_chart_generic(
                ax, f_data, f_err, 'EI', 'EI_Unc', 'blue', 
                'Absolute EI' if is_bottom else '', (0.8, 2.0)
            )
            ax.set_title(f'{fault}', fontweight='bold')
            if i % ncols > 0: ax.tick_params(labelleft=False)
            ax.text(0.02, 0.98, f'({chr(97+i)})', transform=ax.transAxes, fontweight='bold', va='top')
    
        # Normalized EI Plots
        offset = len(fault_order)
        for i, fault in enumerate(fault_order):
            ax = fig.add_subplot(total_plot_rows, ncols, ((nrows + i // ncols) * ncols) + i % ncols + 1)
            f_data = combined_df[combined_df['Fault'] == fault]
            f_err = norm_error_data[norm_error_data['Fault'] == fault]
            is_bottom = ((i // ncols + 1) * ncols + i % ncols) >= len(fault_order)
            
            visualization.plot_ei_step_chart_generic(
                ax, f_data, f_err, 'EI_Normalized', 'EI_Normalized_Unc', 'green', 
                'Normalized EI' if is_bottom else '', (0.4, 1.2)
            )
            ax.set_title(f'{fault}', fontweight='bold')
            if i % ncols > 0: ax.tick_params(labelleft=False)
            ax.text(0.02, 0.98, f'({chr(97+offset+i)})', transform=ax.transAxes, fontweight='bold', va='top')
    
        # Legend Slot
        ax_leg = fig.add_subplot(total_plot_rows, ncols, total_plot_rows * ncols)
        ax_leg.axis('off')
        present_horizons = sorted([h for h in combined_df['Horizon'].unique() if h in config.HORIZON_COLORS and h != 'Tertiary Base'],
                                 key=lambda h: config.HORIZON_AGES.get(h, 99))
        
        legend_elements = [Patch(facecolor=config.HORIZON_COLORS[h], edgecolor='black', alpha=0.5, label=config.HORIZON_DISPLAY_NAMES.get(h, h))
                          for h in present_horizons]
        ax_leg.legend(handles=legend_elements, loc='center', fontsize=9, frameon=False, title="Units")
    
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'EI_Comparison.png'), dpi=300)
        plt.close(fig)

    # 3. Final Displacement Profiles
    print("Generating Final Displacement Profiles...")
    fault_dict = {df['Source_File'].iloc[0]: df for df in fault_dfs}
    plt.rcParams.update({'font.size': 8})
    fig = plt.figure(figsize=(config.FIGURE_WIDTH_2COL_INCH, config.FIGURE_WIDTH_2COL_INCH * 0.6))
    gs = gridspec.GridSpec(2, 10, figure=fig, height_ratios=[1, 1.2], wspace=0.3, hspace=0.3) 
    
    direction_labels = {
        '1A': ('N', 'S'), '1B': ('N', 'S'), '1C': ('N', 'S'), '1D': ('N', 'S'), '1E': ('N', 'S'),
        '2A': ('W', 'E'), '2B': ('W', 'E')
    }

    # Top Row (1A, 1B, 1C, 2B, 2A)
    for i, fault in enumerate(['1A', '1B', '1C', '2B', '2A']):
        ax = fig.add_subplot(gs[0, i*2 : (i+1)*2])
        if fault in fault_dict:
            df = fault_dict[fault]
            
            # Apply Exclusions
            ex_file = os.path.join(base_dir, 'manual_paths', f'{fault}_exclude.json')
            if os.path.exists(ex_file):
                import json
                with open(ex_file, 'r') as f:
                    for exc in json.load(f):
                        df = df[~((df['Horizon'] == exc['Horizon']) & (abs(df['Distance'] - exc['Distance']) < 0.1))]
            
            visualization.plot_displacement_profile(ax, df, show_legend=False, show_xlabel=False, 
                                                  show_ylabel=(i==0), y_limits=(0, 400))
            if i > 0: ax.tick_params(labelleft=False)
            ax.text(0.02, 0.96, f'({chr(97+i)}) {fault}', transform=ax.transAxes, fontweight='bold', fontsize=8, va='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
            d = direction_labels.get(fault, ('',''))
            ax.text(0.0, 1.05, d[0], transform=ax.transAxes, fontweight='bold', fontsize=8, va='bottom', ha='left')
            ax.text(1.0, 1.05, d[1], transform=ax.transAxes, fontweight='bold', fontsize=8, va='bottom', ha='right')

    # Bottom Row (1D, 1E + Legend)
    # 1D
    ax_1d = fig.add_subplot(gs[1, 0:4])
    if '1D' in fault_dict:
        df = fault_dict['1D']
        df = pd.concat([df[df['Horizon'] != 'Tertiary_Base'], processing.remove_outliers(df[df['Horizon'] == 'Tertiary_Base'], threshold=50.0)]).sort_values(['Horizon', 'Distance'])
        visualization.plot_displacement_profile(ax_1d, df, show_legend=False, y_limits=(0, 900))
        ax_1d.text(0.02, 0.96, '(f) 1D', transform=ax_1d.transAxes, fontweight='bold', fontsize=8, va='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
        d = direction_labels.get('1D', ('',''))
        ax_1d.text(0.0, 1.05, d[0], transform=ax_1d.transAxes, fontweight='bold', fontsize=8, va='bottom', ha='left')
        ax_1d.text(1.0, 1.05, d[1], transform=ax_1d.transAxes, fontweight='bold', fontsize=8, va='bottom', ha='right')

    # 1E
    ax_1e = fig.add_subplot(gs[1, 4:8])
    if '1E' in fault_dict:
        df = fault_dict['1E']
        ex_file = os.path.join(base_dir, 'manual_paths', '1E_exclude.json')
        if os.path.exists(ex_file):
            import json
            with open(ex_file, 'r') as f:
                for exc in json.load(f):
                    df = df[~((df['Horizon'] == exc['Horizon']) & (abs(df['Distance'] - exc['Distance']) < 0.1))]
        visualization.plot_displacement_profile(ax_1e, df, show_legend=False, show_ylabel=False, y_limits=(0, 900))
        ax_1e.tick_params(labelleft=False)
        ax_1e.text(0.02, 0.96, '(g) 1E', transform=ax_1e.transAxes, fontweight='bold', fontsize=8, va='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
        d = direction_labels.get('1E', ('',''))
        ax_1e.text(0.0, 1.05, d[0], transform=ax_1e.transAxes, fontweight='bold', fontsize=8, va='bottom', ha='left')
        ax_1e.text(1.0, 1.05, d[1], transform=ax_1e.transAxes, fontweight='bold', fontsize=8, va='bottom', ha='right')

    # Legend
    ax_leg = fig.add_subplot(gs[1, 8:10]); ax_leg.axis('off')
    
    seen_labels = set()
    legend_lines = []
    for h in sorted(config.HORIZON_TOPS_DISPLAY_NAMES.keys(), key=lambda x: config.HORIZON_AGES.get(x, 99)):
        label = config.HORIZON_TOPS_DISPLAY_NAMES.get(h, h)
        if h in config.HORIZON_COLORS and h not in ['Surface', 'Q_Base', 'Quaternary_Base', 'Quaternary Base'] and label not in seen_labels and label != 'Quaternary Base':
            legend_lines.append(Line2D([0],[0], color=config.HORIZON_COLORS[h], lw=2, label=label))
            seen_labels.add(label)
            
    ax_leg.legend(handles=legend_lines, loc='center left', bbox_to_anchor=(0.2, 0.5), fontsize=9, frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Displacement_Profiles.png'), dpi=300)
    plt.close(fig)
    print("Analysis Complete.")

if __name__ == "__main__":
    main()
