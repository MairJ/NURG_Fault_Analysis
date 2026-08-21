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
        # Order matches displacement profiles grouping: (1A,1B,1C) | (2B,2A) | (1D,1E)
        fault_order = ['1A', '1B', '1C', '2B', '2A', '1D', '1E']
        n_faults = len(fault_order)

        # Distinct colours — consistent across row 0 and row 1
        fault_colors = dict(zip(fault_order, plt.cm.tab10.colors[:n_faults]))

        # Cross-fault groups: (panel_letter, faults, column_slice)
        fault_groups = [
            ('h', ['1A', '1B', '1C'], slice(0, 3)),
            ('i', ['2B', '2A'],       slice(3, 5)),
            ('j', ['1D', '1E'],       slice(5, 7)),
        ]

        plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 8})
        from matplotlib.ticker import MultipleLocator

        fig = plt.figure(figsize=(config.FIGURE_WIDTH_2COL_INCH,
                                  config.FIGURE_WIDTH_2COL_INCH * 0.78))
        # 3 rows: per-fault absolute EI | 3 group cross-fault panels | legend strip
        gs_ei = gridspec.GridSpec(3, n_faults, figure=fig,
                                  height_ratios=[1, 1.5, 0.12],
                                  hspace=0.55, wspace=0.25)

        # Pre-compute per-group x-limits from actual normalised EI data
        group_xlims = {}
        for g_letter, g_faults, _ in fault_groups:
            vals_all = []
            for gf in g_faults:
                v = combined_df[combined_df['Fault'] == gf]['EI_Normalized'].dropna().values
                vals_all.extend(v)
            if vals_all:
                lo, hi = min(vals_all), max(vals_all)
                pad = max((hi - lo) * 0.08, 0.02)
                group_xlims[g_letter] = (lo - pad, hi + pad)
            else:
                group_xlims[g_letter] = (0.4, 1.1)

        for i, fault in enumerate(fault_order):
            ax = fig.add_subplot(gs_ei[0, i])
            f_data = combined_df[combined_df['Fault'] == fault]
            f_err  = error_data[error_data['Fault'] == fault]

            visualization.plot_ei_step_chart_generic(
                ax, f_data, f_err, 'EI', 'EI_Unc', 'steelblue',
                'Absolute EI' if i == n_faults // 2 else '', (0.8, 2.0)
            )
            ax.text(-0.08, 1.08, f'({chr(97 + i)})', transform=ax.transAxes,
                    fontweight='bold', fontsize=8, va='bottom', ha='left')
            ax.set_title(fault, fontsize=8, fontweight='bold', pad=2)
            if i > 0:
                ax.tick_params(labelleft=False)
                ax.set_ylabel('')
            ax.xaxis.set_major_locator(MultipleLocator(0.5))
            ax.tick_params(axis='x', labelsize=7)

        for g_idx, (letter, faults, col_slice) in enumerate(fault_groups):
            ax_g = fig.add_subplot(gs_ei[1, col_slice])

            for fault in faults:
                f_data = combined_df[combined_df['Fault'] == fault].copy().sort_values('Age (Ma)')
                last_age = f_data.iloc[-1]['Age (Ma)']
                next_ages = [a for a in sorted(config.HORIZON_AGES.values()) if a > last_age]
                if next_ages:
                    nr = f_data.iloc[-1].copy()
                    nr['Age (Ma)'] = next_ages[0]
                    f_data = pd.concat([f_data, pd.DataFrame([nr])], ignore_index=True)

                step_x, step_y = [], []
                ages = f_data['Age (Ma)'].values
                vals = f_data['EI_Normalized'].values
                if len(ages) > 0:
                    step_x.append(vals[0]); step_y.append(ages[0])
                    for j in range(len(ages) - 1):
                        step_x.append(vals[j]);     step_y.append(ages[j + 1])
                        step_x.append(vals[j + 1]); step_y.append(ages[j + 1])

                ax_g.plot(step_x, step_y, color=fault_colors[fault],
                          lw=1.8, alpha=0.8, label=fault)

                # Label at the top of the line (just above the axes frame)
                if len(vals) > 0:
                    ax_g.text(vals[0], -1.5, fault,
                              va='bottom', ha='center', fontsize=7,
                              fontweight='bold', color=fault_colors[fault],
                              clip_on=False)

            ax_g.axvline(1.0, color='black', ls='--', lw=0.8, alpha=0.6)
            ax_g.set_xlim(*group_xlims[letter])
            ax_g.set_ylim(40, 0)
            ax_g.set_xlabel('Normalised EI', fontsize=8)
            ax_g.grid(True, ls='--', lw=0.3, alpha=0.4)
            if g_idx == 0:
                ax_g.set_ylabel('Age (Ma)', fontsize=8)
            else:
                ax_g.tick_params(labelleft=False)
                ax_g.set_ylabel('')
            ax_g.text(-0.04, 1.06, f'({letter})', transform=ax_g.transAxes,
                      fontweight='bold', fontsize=8, va='bottom', ha='right')

        ax_leg = fig.add_subplot(gs_ei[2, :])
        ax_leg.axis('off')
        present_horizons = sorted(
            [h for h in combined_df['Horizon'].unique()
             if h in config.HORIZON_COLORS and h != 'Tertiary Base'],
            key=lambda h: config.HORIZON_AGES.get(h, 99)
        )
        legend_elements = [
            Patch(facecolor=config.HORIZON_COLORS[h], edgecolor='0.4', alpha=0.5,
                  label=config.HORIZON_DISPLAY_NAMES.get(h, h))
            for h in present_horizons
        ]
        ax_leg.legend(handles=legend_elements, loc='center',
                      ncol=len(legend_elements), fontsize=8,
                      frameon=False, handlelength=1.2, columnspacing=0.8)

        fig.subplots_adjust(left=0.07, right=0.97, top=0.94, bottom=0.03)
        plt.savefig(os.path.join(output_dir, 'EI_Comparison.png'), dpi=300)
        plt.savefig(os.path.join(output_dir, 'Figure_7_EI_Comparison.png'), dpi=300)
        plt.savefig(os.path.join(output_dir, 'Figure_7_EI_Comparison.svg'))
        plt.close(fig)

    # 3. Final Displacement Profiles
    print("Generating Final Displacement Profiles...")
    fault_dict = {df['Source_File'].iloc[0]: df for df in fault_dfs}
    plt.rcParams.update({'font.size': 8})

    # Exact fault trace lengths (km) from data — panel widths are proportional to these
    # Row 1 total: ~27.78 km  |  Row 2 total: ~27.10 km  (nearly equal → both rows same width)
    fault_lengths = {'1A': 8.95, '1B': 5.31, '1C': 4.28,
                     '2B': 5.82, '2A': 3.42,
                     '1D': 17.42, '1E': 9.68}

    row1_faults = ['1A', '1B', '1C', '2B', '2A']
    row2_faults = ['1D', '1E']
    grid_ncols = 20  # fine-grained grid for proportional widths

    def to_int_cols(faults, total):
        """Round fault lengths to integer column counts summing exactly to total."""
        lengths = [fault_lengths[f] for f in faults]
        total_len = sum(lengths)
        raw = [l / total_len * total for l in lengths]
        cols = [max(1, int(r)) for r in raw]
        diff = total - sum(cols)
        fracs = sorted(range(len(raw)), key=lambda i: raw[i] - int(raw[i]), reverse=True)
        for i in range(abs(diff)):
            cols[fracs[i % len(fracs)]] += 1 if diff > 0 else -1
        return cols

    row1_cols = to_int_cols(row1_faults, grid_ncols)   # [6, 4, 3, 4, 3]
    row2_cols = to_int_cols(row2_faults, grid_ncols)    # [13, 7]

    # Per-fault y-limits (2A uses compressed scale; note in caption)
    y_limits_map = {
        '1A': (0, 400), '1B': (0, 400), '1C': (0, 400),
        '2B': (0, 400), '2A': (0, 100)
    }
    # Per-fault x-tick spacing (1 km for short profiles, 2 km for long ones)
    tick_map = {
        '1A': 2, '1B': 1, '1C': 1, '2B': 1, '2A': 1, '1D': 2, '1E': 2
    }
    direction_labels = {
        '1A': ('N', 'S'), '1B': ('N', 'S'), '1C': ('N', 'S'), '1D': ('N', 'S'), '1E': ('N', 'S'),
        '2A': ('W', 'E'), '2B': ('W', 'E')
    }

    fig = plt.figure(figsize=(config.FIGURE_WIDTH_2COL_INCH, config.FIGURE_WIDTH_2COL_INCH * 0.72))
    # 3 rows: top faults, bottom faults, thin horizontal legend strip
    gs = gridspec.GridSpec(3, grid_ncols, figure=fig,
                           height_ratios=[1, 1.5, 0.15],
                           hspace=0.5)

    # ── Top Row (1A, 1B, 1C, 2B, 2A) — widths proportional to fault length ──
    col = 0
    for i, (fault, width) in enumerate(zip(row1_faults, row1_cols)):
        ax = fig.add_subplot(gs[0, col:col + width])
        col += width
        if fault not in fault_dict:
            continue
        df = fault_dict[fault]

        # Apply exclusions
        ex_file = os.path.join(base_dir, 'manual_paths', f'{fault}_exclude.json')
        if os.path.exists(ex_file):
            import json
            with open(ex_file, 'r') as f:
                for exc in json.load(f):
                    df = df[~((df['Horizon'] == exc['Horizon']) & (abs(df['Distance'] - exc['Distance']) < 0.1))]

        visualization.plot_displacement_profile(ax, df, show_legend=False, show_xlabel=False,
                                               show_ylabel=(i == 0),
                                               y_limits=y_limits_map.get(fault, (0, 400)),
                                               x_tick_spacing=tick_map.get(fault, 2))
        # 2A: different scale → right-side y-axis to make scale difference explicit
        if fault == '2A':
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position('right')
            ax.set_ylabel('Fault throw (m)', fontsize=8)
        elif i > 0:
            ax.tick_params(labelleft=False)

        # Panel letter above top-left corner (outside frame, never overlaps data)
        ax.text(-0.02, 1.09, f'({chr(97 + i)})', transform=ax.transAxes,
                fontweight='bold', fontsize=8, va='bottom', ha='left')
        # Fault name as centred title
        ax.set_title(fault, fontsize=8, fontweight='bold', pad=2)
        # Compass directions inside top corners of the panel
        d = direction_labels.get(fault, ('', ''))
        ax.text(0.03, 0.97, d[0], transform=ax.transAxes, fontweight='bold', fontsize=7,
                va='top', ha='left', color='0.35')
        ax.text(0.97, 0.97, d[1], transform=ax.transAxes, fontweight='bold', fontsize=7,
                va='top', ha='right', color='0.35')

    col = 0
    ax_1d = fig.add_subplot(gs[1, col:col + row2_cols[0]]); col += row2_cols[0]
    ax_1e = fig.add_subplot(gs[1, col:col + row2_cols[1]])

    if '1D' in fault_dict:
        df = fault_dict['1D']
        df = pd.concat([df[df['Horizon'] != 'Tertiary_Base'],
                        processing.remove_outliers(df[df['Horizon'] == 'Tertiary_Base'],
                                                   threshold=50.0)]
                       ).sort_values(['Horizon', 'Distance'])
        visualization.plot_displacement_profile(ax_1d, df, show_legend=False, y_limits=(0, 900),
                                               x_tick_spacing=tick_map['1D'])
        ax_1d.text(-0.02, 1.09, '(f)', transform=ax_1d.transAxes,
                   fontweight='bold', fontsize=8, va='bottom', ha='left')
        ax_1d.set_title('1D', fontsize=8, fontweight='bold', pad=2)
        d = direction_labels['1D']
        ax_1d.text(0.03, 0.97, d[0], transform=ax_1d.transAxes, fontweight='bold', fontsize=7,
                   va='top', ha='left', color='0.35')
        ax_1d.text(0.97, 0.97, d[1], transform=ax_1d.transAxes, fontweight='bold', fontsize=7,
                   va='top', ha='right', color='0.35')

    if '1E' in fault_dict:
        df = fault_dict['1E']
        ex_file = os.path.join(base_dir, 'manual_paths', '1E_exclude.json')
        if os.path.exists(ex_file):
            import json
            with open(ex_file, 'r') as f:
                for exc in json.load(f):
                    df = df[~((df['Horizon'] == exc['Horizon']) & (abs(df['Distance'] - exc['Distance']) < 0.1))]
        visualization.plot_displacement_profile(ax_1e, df, show_legend=False, show_ylabel=False,
                                               y_limits=(0, 900), x_tick_spacing=tick_map['1E'])
        ax_1e.tick_params(labelleft=False)
        ax_1e.text(-0.02, 1.09, '(g)', transform=ax_1e.transAxes,
                   fontweight='bold', fontsize=8, va='bottom', ha='left')
        ax_1e.set_title('1E', fontsize=8, fontweight='bold', pad=2)
        d = direction_labels['1E']
        ax_1e.text(0.03, 0.97, d[0], transform=ax_1e.transAxes, fontweight='bold', fontsize=7,
                   va='top', ha='left', color='0.35')
        ax_1e.text(0.97, 0.97, d[1], transform=ax_1e.transAxes, fontweight='bold', fontsize=7,
                   va='top', ha='right', color='0.35')

    ax_leg = fig.add_subplot(gs[2, :])
    ax_leg.axis('off')

    seen_labels = set()
    legend_lines = []
    for h in sorted(config.HORIZON_TOPS_DISPLAY_NAMES.keys(), key=lambda x: config.HORIZON_AGES.get(x, 99)):
        label = config.HORIZON_TOPS_DISPLAY_NAMES.get(h, h)
        if (h in config.HORIZON_COLORS and
                h not in ['Surface', 'Q_Base', 'Quaternary_Base', 'Quaternary Base'] and
                label not in seen_labels and label != 'Quaternary Base'):
            legend_lines.append(Line2D([0], [0], color=config.HORIZON_COLORS[h], lw=2, label=label))
            seen_labels.add(label)

    ax_leg.legend(handles=legend_lines, loc='center', ncol=len(legend_lines),
                  fontsize=8, frameon=False, handlelength=1.5, columnspacing=0.8)

    fig.subplots_adjust(left=0.07, right=0.91, top=0.93, bottom=0.03)
    plt.savefig(os.path.join(output_dir, 'Displacement_Profiles.png'), dpi=300)
    plt.savefig(os.path.join(output_dir, 'Figure_6_Displacement_Profiles.png'), dpi=300)
    plt.savefig(os.path.join(output_dir, 'Figure_6_Displacement_Profiles.svg'))
    plt.close(fig)
    print("Analysis Complete.")

if __name__ == "__main__":
    main()
