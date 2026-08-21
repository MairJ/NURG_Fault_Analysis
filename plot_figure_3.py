import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from obspy.io.segy.segy import _read_segy
import os
from matplotlib.ticker import MultipleLocator
import geopandas as gpd
import mplstereonet

# Base directory for the new sections
base_dir = r'..\segy\new'

# File names
file_1_segy = os.path.join(base_dir, 'xsec_shp_1A1B1C.segy')
file_2_segy = os.path.join(base_dir, 'xsec_shp_1D1E.segy')
file_3_segy = os.path.join(base_dir, 'xsec_shp_2A2B.segy')

file_1_shp = os.path.join(base_dir, 'xsec_shp_1A1B1C.shp')
file_2_shp = os.path.join(base_dir, 'xsec_shp_1D1E.shp')
file_3_shp = os.path.join(base_dir, 'xsec_shp_2A2B.shp')

ts_dir = r'..\stereonets\Fault_surface_Stereonet\Petrel_output'
ts_files = [os.path.join(ts_dir, f) for f in os.listdir(ts_dir) if f.endswith('.ts')]

custom_cmap = 'seismic'

def get_strike_dip_arrays(filepath):
    """Calculates the strike and dip for every triangle in the .ts mesh."""
    vertices = {}
    strikes = []
    dips = []
    
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == 'VRTX':
                vid = int(parts[1])
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                vertices[vid] = np.array([x, y, z])
            elif parts[0] == 'TRGL':
                v1, v2, v3 = int(parts[1]), int(parts[2]), int(parts[3])
                if v1 in vertices and v2 in vertices and v3 in vertices:
                    p1, p2, p3 = vertices[v1], vertices[v2], vertices[v3]
                    normal = np.cross(p2 - p1, p3 - p1)
                    norm_length = np.linalg.norm(normal)
                    if norm_length > 0:
                        normal = normal / norm_length
                        # Ensure normal points UP
                        if normal[2] < 0:
                            normal = -normal
                        # Dip angle
                        dip = np.degrees(np.arccos(normal[2]))
                        # Dip direction
                        dip_dir = np.degrees(np.arctan2(normal[0], normal[1])) % 360
                        strike = (dip_dir - 90) % 360
                        strikes.append(strike)
                        dips.append(dip)
    return np.array(strikes), np.array(dips)

def load_segy_data(file_path):
    print(f"Loading {file_path}...")
    stream = _read_segy(file_path)
    data = [trace.data for trace in stream.traces]
    return np.transpose(data)

def plot_profile(ax, data, sample_numbers, title, start_km, end_km, profile_distance_km, 
                 label_start='W', label_end='E', letter='(a)', vmin=-15, vmax=15, alpha=1.0, line_color='black'):
    
    cropped_dist = end_km - start_km

    # Image plot
    im = ax.imshow(
        data,
        aspect='auto',
        cmap=custom_cmap,
        extent=[0, cropped_dist, sample_numbers[-1], sample_numbers[0]],
        vmin=vmin,
        vmax=vmax,
        alpha=alpha,
        interpolation='nearest'
    )
    
    # Title on top, color coded to the map
    ax.set_title(title, color=line_color, fontweight='bold', fontsize=10)
    
    # Mark the top of the section with the corresponding color
    ax.spines['top'].set_color(line_color)
    ax.spines['top'].set_linewidth(2)
    
    # Labels
    ax.set_xlabel('Distance (km)', fontsize=10)
    ax.set_ylabel('Depth (km)', fontsize=10)
    
    # Y-limits
    ax.set_ylim([-4, 0]) 
    
    # X-limits: dynamically cropped from 0
    ax.set_xlim([0, cropped_dist])
    
    # Add start/end labels above the plot corners
    ax.text(0.02, 1.02, label_start, transform=ax.transAxes, fontweight='bold', fontsize=12, 
            ha='left', va='bottom', color='black')
    ax.text(0.98, 1.02, label_end, transform=ax.transAxes, fontweight='bold', fontsize=12, 
            ha='right', va='bottom', color='black')
            
    # Subplot letter at top-left inside to match a, b, d
    ax.text(0.02, 0.96, letter, transform=ax.transAxes, fontweight='bold', fontsize=10, 
            ha='left', va='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    
    ax.tick_params(axis='both', which='major', labelsize=8)

    # Set y-ticks and labels to display positive depth values (or standard negative)
    ax.xaxis.set_major_locator(MultipleLocator(5)) 
    ax.yaxis.set_major_locator(MultipleLocator(1)) 
    
    yticks = np.linspace(-4, 0, num=5) 
    ytick_labels = [f"{abs(tick):.0f}" for tick in yticks] 
    ax.set_yticks(yticks)
    ax.set_yticklabels(ytick_labels)
    
    # Uniform Grid - FAI and EI style
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)

from matplotlib.ticker import MaxNLocator

def crop_segy_data(data, profile_distance_km, manual_start_trace=0):
    # data is (samples, traces)
    trace_energy = np.sum(np.abs(data), axis=0)
    
    # Only consider traces after manual_start_trace
    nonzero = np.where(trace_energy[manual_start_trace:] > 0)[0]
    
    if len(nonzero) == 0:
        return data, 0, profile_distance_km
        
    first = manual_start_trace + nonzero[0]
    
    # For the end, we still search from the very end of the array
    nonzero_all = np.where(trace_energy > 0)[0]
    last = nonzero_all[-1]
    
    trace_width_km = profile_distance_km / data.shape[1]
    start_km = first * trace_width_km
    end_km = (last + 1) * trace_width_km
    
    cropped_data = data[:, first:last+1]
    return cropped_data, start_km, end_km

def main():
    # Load shapefiles to get lengths and for map plotting
    gdf_1 = gpd.read_file(file_1_shp)
    gdf_2 = gpd.read_file(file_2_shp)
    gdf_3 = gpd.read_file(file_3_shp)
    
    dist_1_km = gdf_1.length.sum() / 1000.0
    dist_2_km = gdf_2.length.sum() / 1000.0
    dist_3_km = gdf_3.length.sum() / 1000.0

    # Load the SEG-Y data
    data_1 = load_segy_data(file_1_segy)
    data_2 = load_segy_data(file_2_segy)
    data_3 = load_segy_data(file_3_segy)
    
    # Flip 1A-1B-1C (data_1) to plot SW to NE (West to East)
    data_1 = np.fliplr(data_1)
    # Flip 1D-1E (data_2) to plot West to East
    data_2 = np.fliplr(data_2)
    
    # Crop empty traces, and force 2A-2B (data_3) to skip the southern part
    data_1, start_1, end_1 = crop_segy_data(data_1, dist_1_km)
    data_2, start_2, end_2 = crop_segy_data(data_2, dist_2_km)
    data_3, start_3, end_3 = crop_segy_data(data_3, dist_3_km, manual_start_trace=900)

    depth_per_sample = 6 / 1000  # 6m = 0.006 km
    
    sample_numbers_1 = [-i * depth_per_sample for i in range(data_1.shape[0])]
    sample_numbers_2 = [-i * depth_per_sample for i in range(data_2.shape[0])]
    sample_numbers_3 = [-i * depth_per_sample for i in range(data_3.shape[0])]

    # Set up optimized layout using a 26-column grid
    # Scale: 1 column = 1 km.
    # 1D-1E cropped width ~ 10 km
    # 1A-1B-1C cropped width ~ 19.5 km
    # 2A-2B cropped width ~ 12.3 km (after Northern crop)
    fig = plt.figure(figsize=(18, 12), dpi=600)
    gs = gridspec.GridSpec(3, 26, height_ratios=[1, 1, 1], hspace=0.4, wspace=1.0)

    # MAP PLOT (Spans 2 rows, cols 0-8)
    ax_map = fig.add_subplot(gs[0:2, 0:8])
    
    # Crop shapefiles to match the non-empty SEGY traces plotted
    from shapely.ops import substring
    # 1A-1B-1C was flipped, so we measure its valid segment from the NE (start of shapefile)
    gdf_1.loc[0, 'geometry'] = substring(gdf_1.geometry.iloc[0], (dist_1_km - end_1) * 1000, (dist_1_km - start_1) * 1000)
    # 1D-1E was flipped, so we measure its valid segment from the East (start of shapefile)
    gdf_2.loc[0, 'geometry'] = substring(gdf_2.geometry.iloc[0], (dist_2_km - end_2) * 1000, (dist_2_km - start_2) * 1000)
    gdf_3.loc[0, 'geometry'] = substring(gdf_3.geometry.iloc[0], start_3 * 1000, end_3 * 1000)
    
    # Plot shapefiles on map
    gdf_1.plot(ax=ax_map, color='red', linewidth=2)
    gdf_2.plot(ax=ax_map, color='blue', linewidth=2)
    gdf_3.plot(ax=ax_map, color='green', linewidth=2)
    
    # Load and plot 3D boundary polygon
    poly_path = r"C:\Users\mair\Nextcloud\00_Share\NURG_exchange\Shapefile\3D_limit.shp"
    if os.path.exists(poly_path):
        gdf_poly = gpd.read_file(poly_path)
        gdf_poly.plot(ax=ax_map, facecolor='none', edgecolor='black', linewidth=1.5, linestyle='--')
    
    # Label the lines directly on the map
    bbox_style = dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1)
    
    import math
    def get_line_angle(line):
        coords = list(line.coords)
        p1, p2 = coords[0], coords[-1]
        angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
        if angle > 90: angle -= 180
        elif angle < -90: angle += 180
        return angle
        
    line1 = gdf_1.geometry.iloc[0]
    m1 = line1.interpolate(0.5, normalized=True)
    ax_map.text(m1.x, m1.y, '1A-1B-1C', color='red', fontweight='bold', fontsize=9, ha='center', va='bottom', bbox=bbox_style, rotation=get_line_angle(line1))
    
    line2 = gdf_2.geometry.iloc[0]
    m2 = line2.interpolate(0.5, normalized=True)
    ax_map.text(m2.x, m2.y, '1D-1E', color='blue', fontweight='bold', fontsize=9, ha='center', va='bottom', bbox=bbox_style, rotation=get_line_angle(line2))
    
    line3 = gdf_3.geometry.iloc[0]
    m3 = line3.interpolate(0.8, normalized=True) # slightly offset for 2A-2B
    ax_map.text(m3.x, m3.y, '2A-2B', color='green', fontweight='bold', fontsize=9, ha='left', va='center', bbox=bbox_style, rotation=get_line_angle(line3))
    
    ax_map.set_xlabel("Easting", fontsize=8)
    ax_map.set_ylabel("Northing", fontsize=8)
    
    # Reduce ticks and explicitly set rotation to 0 for x, 90 for y
    ax_map.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax_map.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax_map.tick_params(axis='x', which='major', labelsize=8, labelrotation=0)
    ax_map.tick_params(axis='y', which='major', labelsize=8, labelrotation=90)
    ax_map.ticklabel_format(style='plain') # Avoid scientific notation for coordinates
    
    ax_map.grid(True, linestyle='--', alpha=0.5)
    
    ax_map.text(0.02, 0.98, '(a)', transform=ax_map.transAxes, fontweight='bold', fontsize=10, 
            va='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # SEISMIC SECTIONS
    
    # Section 1D-1E (~10 km cropped) -> Row 0, cols 16-26 (10 cols)
    ax_sec2 = fig.add_subplot(gs[0, 16:26])
    plot_profile(ax_sec2, data_2, sample_numbers_2, "Section 1D-1E", start_2, end_2, dist_2_km, 
                 label_start='W', label_end='E', letter='(c)', line_color='blue')

    # Section 2A-2B (~12.3 km cropped) -> Row 1, cols 14-26 (12 cols)
    ax_sec3 = fig.add_subplot(gs[1, 14:26])
    plot_profile(ax_sec3, data_3, sample_numbers_3, "Section 2A-2B", start_3, end_3, dist_3_km, 
                 label_start='SSW', label_end='NNE', letter='(e)', line_color='green')

    # Section 1A-1B-1C (~19.5 km cropped) -> Row 2, cols 0-20 (20 cols)
    ax_sec1 = fig.add_subplot(gs[2, 0:20])
    plot_profile(ax_sec1, data_1, sample_numbers_1, "Section 1A-1B-1C", start_1, end_1, dist_1_km, 
                 label_start='SW', label_end='NE', letter='(f)', line_color='red')

    # STEREONET PLOT (Row 0, cols 8-14)
    ax_stereo = fig.add_subplot(gs[0, 8:14], projection='stereonet')
    
    # ROSE DIAGRAM (Row 1, cols 8-14)
    ax_rose = fig.add_subplot(gs[1, 8:14], projection='polar')
    ax_rose.set_theta_zero_location('N')
    ax_rose.set_theta_direction(-1) # Clockwise
    
    # Map the fault stereonet colors to match parent sections (Red, Blue, Green)
    # These colors are specifically chosen to avoid clashing with the JTI-TB horizon palette
    color_map = {
        '1A': 'maroon', '1B': 'red', '1C': 'coral',
        '1D': 'navy', '1E': 'deepskyblue', 
        '2A': 'darkgreen', '2B': 'yellowgreen'
    }
    
    import matplotlib.lines as mlines
    legend_elements = []
    all_strikes = []
    
    for ts_file in ts_files:
        fault_name = os.path.basename(ts_file).replace('.ts', '')
        strikes, dips = get_strike_dip_arrays(ts_file)
        
        if len(strikes) < 3: continue
            
        color = color_map.get(fault_name, 'gray')
        all_strikes.extend(strikes)
        
        try:
            ax_stereo.density_contour(strikes, dips, measurement='poles', levels=[0.2], colors=[color], linewidths=2)
            legend_elements.append(mlines.Line2D([0], [0], color=color, lw=2, label=fault_name))
        except Exception:
            pass
            
    ax_stereo.grid(True, linestyle='-', alpha=0.5)
    
    if legend_elements:
        ax_stereo.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1.15, 0.5), 
                         fontsize=8, frameon=False, title='Faults', title_fontproperties={'weight':'bold', 'size':9})
    
    # Hide '315' tick entirely to prevent overlap with the (b) letter
    ax_stereo.set_azimuth_ticks(np.arange(0, 271, 45))
    
    ax_stereo.text(0.02, 0.98, '(b)', transform=ax_stereo.transAxes, fontweight='bold', fontsize=10, 
            va='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # Plot Rose Diagram
    if all_strikes:
        strikes_rad = np.radians(all_strikes)
        strikes_rad_opp = np.radians((np.array(all_strikes) + 180) % 360)
        combined_rad = np.concatenate([strikes_rad, strikes_rad_opp])
        
        bin_edges = np.arange(0, 2*np.pi + np.pi/18, np.pi/18) # 10 degree bins
        hist, _ = np.histogram(combined_rad, bins=bin_edges)
        width = np.pi/18
        
        ax_rose.bar(bin_edges[:-1], hist, width=width, bottom=0.0, color='gray', edgecolor='black', alpha=0.7, align='edge')
        ax_rose.set_yticklabels([]) # Hide radial ticks
        ax_rose.set_xticks(np.pi/180. * np.linspace(0,  360, 8, endpoint=False))
        # Hide 'E' and 'NW' labels to prevent layout overlaps
        ax_rose.set_xticklabels(['N', 'NE', '', 'SE', 'S', 'SW', 'W', ''], fontsize=8)
        
    ax_rose.text(0.02, 0.98, '(d)', transform=ax_rose.transAxes, fontweight='bold', fontsize=10, 
            va='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    # Add legend to Row 2, Cols 20-26
    ax_legend = fig.add_subplot(gs[2, 20:26])
    ax_legend.axis('off')
    
    from matplotlib.lines import Line2D
    
    legend_elements = [
        Line2D([0], [0], color='#1b9e77', lw=2, label='JTII Top'),
        Line2D([0], [0], color='#d95f02', lw=2, label='JTI Top'),
        Line2D([0], [0], color='#7570b3', lw=2, label='OHY Top'),
        Line2D([0], [0], color='#e7298a', lw=2, label='UHY Top'),
        Line2D([0], [0], color='#66a61e', lw=2, label='CBS Top'),
        Line2D([0], [0], color='#e6ab02', lw=2, label='BNS Top'),
        Line2D([0], [0], color='#a6761d', lw=2, label='RT Top'),
        Line2D([0], [0], color='black', lw=2, label='TB'),
        Line2D([0], [0], color='black', lw=2, linestyle='--', label='Basement'),
        Line2D([0], [0], color='black', lw=2, label='Faults'),
        Line2D([0], [0], color='red', lw=2, label='Well')
    ]
    
    ax_legend.legend(handles=legend_elements, loc='center', ncol=2, frameon=False, fontsize=10)

    # Adjust layout
    plt.tight_layout(pad=1.5)

    # Save outputs
    output_png = "seismic_profiles_arranged.png"
    plt.savefig(output_png, format='png', dpi=600, bbox_inches='tight')
    
    output_svg = "seismic_profiles_arranged.svg"
    plt.savefig(output_svg, format='svg')
    
    print(f"Plots saved to {output_png} and {output_svg}")

if __name__ == "__main__":
    main()
