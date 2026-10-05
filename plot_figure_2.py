import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import ConnectionPatch
import numpy as np
import segyio

def draw_wavy_line(ax, x_start, x_end, y, amplitude=0.1, frequency=15, color='black', lw=0.5):
    x = np.linspace(x_start, x_end, 500)
    y_wave = y + amplitude * np.sin(frequency * np.pi * (x - x_start))
    ax.plot(x, y_wave, color=color, linewidth=lw)

def add_box(ax, x, y, width, height, text='', color='white', text_color='black', angle=0, fontsize=5, draw_edges=True):
    edge = 'black' if draw_edges else 'none'
    rect = patches.Rectangle((x, y), width, height, linewidth=0.5, edgecolor=edge, facecolor=color)
    ax.add_patch(rect)
    if text:
        cx = x + width / 2
        cy = y + height / 2
        ax.text(cx, cy, text, color=text_color, ha='center', va='center', rotation=angle, fontsize=fontsize)

def main():
    # Set up a figure with two subplots side-by-side
    # EGU Solid Earth 2-column width is exactly 17 cm (6.69 inches).
    # Setting height to ~12 cm (4.72 inches) for a half-page portrait layout.
    fig, (ax_strat, ax_seis) = plt.subplots(1, 2, figsize=(6.69, 4.72), gridspec_kw={'width_ratios': [2, 1]})
    
        # LEFT AXIS: STRATIGRAPHY
    ax_strat.set_ylim(50, -4)
    ax_strat.set_xlim(0, 13)
    ax_strat.axis('off') 
    
    # Titles at exactly the same vertical level
    ax_strat.text(2, 1.02, "Chronostratigraphy", transform=ax_strat.get_xaxis_transform(), ha='center', va='bottom', fontsize=6, fontweight='bold')
    ax_strat.text(6.5, 1.02, "Lithostratigraphy", transform=ax_strat.get_xaxis_transform(), ha='center', va='bottom', fontsize=6, fontweight='bold')
    ax_strat.text(10.5, 1.02, "Interpreted Horizons", transform=ax_strat.get_xaxis_transform(), ha='center', va='bottom', fontsize=6, fontweight='bold')
    
    add_box(ax_strat, 0, 0, 1, 45, 'Cenozoic', color='#F2F91D', angle=90, fontsize=6)
    add_box(ax_strat, 0, 45, 1, 5, 'Pal.', color='#99C08D', angle=90, fontsize=8) 
    
    add_box(ax_strat, 1, 0, 1, 2.58, 'Q', color='#F9F97F', angle=0, fontsize=5)
    add_box(ax_strat, 1, 2.58, 1, 20.45, 'Neogene', color='#FFE619', angle=90, fontsize=6)
    add_box(ax_strat, 1, 23, 1, 22, 'Paleogene', color='#FD9A52', angle=90, fontsize=6)
    add_box(ax_strat, 1, 45, 1, 5, 'Perm', color='#F04028', angle=90, fontsize=8) 
    
    # Series / stage boundaries: ICS International Chronostratigraphic Chart v2023/09 (Ma).
    # The axis is cut at 45 Ma (no scale below); Lutetian base (47.8 Ma) is clipped there.
    series = [  # (top, base, label, colour, rotation)
        (0, 2.58, 'Hol.-' + chr(10) + 'Pleis.', '#FFF2AE', 0),
        (2.58, 5.33, 'Pliocene', '#FFFF99', 0),
        (5.33, 23.03, 'Miocene', '#FFFF00', 90),
        (23.03, 33.9, 'Oligocene', '#FDC07A', 90),
        (33.9, 45, 'Eocene', '#FDB46C', 90),
    ]
    for top, base, lab, col, ang in series:
        add_box(ax_strat, 2, top, 1, base - top, lab, color=col, angle=ang, fontsize=4)
    add_box(ax_strat, 2, 45, 1, 5, 'Upper', color='#FB9A85', fontsize=4)

    stages = [
        (0, 2.58, 'Piac.', '#FFFFBF'), (2.58, 5.33, 'Zanc.', '#FFFFB3'),
        (5.33, 7.25, 'Mess.', '#FFFF73'), (7.25, 11.63, 'Tort.', '#FFFF66'),
        (11.63, 13.82, 'Serr.', '#FFFF59'), (13.82, 15.97, 'Lang.', '#FFFF4D'),
        (15.97, 20.44, 'Burd.', '#FFFF41'), (20.44, 23.03, 'Aqui.', '#FFFF33'),
        (23.03, 28.1, 'Chatt.', '#FEE6AA'), (28.1, 33.9, 'Rup.', '#FED99A'),
        (33.9, 37.71, 'Pria.', '#FDCDA1'), (37.71, 41.03, 'Bart.', '#FDC091'),
        (41.03, 45, 'Lutet.', '#FCB482'),
    ]
    for top, base, lab, col in stages:
        add_box(ax_strat, 3, top, 1, base - top, lab, color=col, fontsize=4)
    add_box(ax_strat, 3, 45, 1, 5, 'Ypre.', color='#FCA773', fontsize=4)

    # Axis break: everything below 45 Ma is NOT to scale
    ax_strat.plot([-0.05, 8.05], [45, 45], color='red', lw=0.6, ls=(0, (4, 2)))
    ax_strat.text(-0.1, 45, 'scale break', color='red', fontsize=3.5, ha='right', va='center')

    ax_strat.plot([4.2, 4.2], [0, 45], color='black', lw=0.5)
    for age in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45]:
        ax_strat.plot([4.2, 4.4], [age, age], color='black', lw=0.5)
        ax_strat.text(4.5, age, str(age), va='center', fontsize=5)
    ax_strat.text(4.5, -1, "Age\n(Ma)", ha='center', fontsize=5)

    # Lithostratigraphy
    add_box(ax_strat, 5, 0, 3, 2.58, 'Quaternary', color='#f4e377', draw_edges=False, fontsize=5)
    add_box(ax_strat, 5, 2.58, 3, 2.72, 'Iffezheim\nFormation', color='#f4e377', draw_edges=False, fontsize=5)
    
    draw_wavy_line(ax_strat, 5, 8, 5.3)
    ax_strat.text(6.5, 10, 'Hiatus', ha='center', va='center', fontsize=6)
    draw_wavy_line(ax_strat, 5, 8, 14)
    
    add_box(ax_strat, 5, 14, 3, 1, 'Weiterstadt Formation', color='#d6af84', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 15, 3, 3, 'Groß-Rohrheim Formation', color='#9eb998', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 18, 1.5, 6, 'Hydrobia\nbeds', color='#a2c6d9', draw_edges=False, fontsize=5)
    add_box(ax_strat, 6.5, 18, 1.5, 3, 'Upper', color='#b2d3c2', draw_edges=False, fontsize=5)
    add_box(ax_strat, 6.5, 21, 1.5, 3, 'Lower', color='#b2d3c2', draw_edges=False, fontsize=5)
    add_box(ax_strat, 5, 24, 3, 1, 'Corbicula beds', color='#c0d0e1', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 25, 3, 1.5, 'Cerithium beds', color='#b8cce4', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 26.5, 3, 1.5, 'Niederrödern beds', color='#e0c38c', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 28, 3, 1, 'Cyrena Marls', color='#b8cce4', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 29, 3, 1.5, 'Meletta beds', color='#539fc4', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 30.5, 3, 1.5, 'Rupel clay', color='#308dbb', draw_edges=False, fontsize=5)
    add_box(ax_strat, 5, 32, 1.5, 3, 'Pechelbronn\nFormation', color='#cad08a', draw_edges=False, fontsize=5)
    add_box(ax_strat, 6.5, 32, 1.5, 1, 'Upper', color='#e7e9a8', draw_edges=False, fontsize=4)
    add_box(ax_strat, 6.5, 33, 1.5, 1, 'Middle', color='#cad08a', draw_edges=False, fontsize=4)
    add_box(ax_strat, 6.5, 34, 1.5, 1, 'Lower', color='#e7e9a8', draw_edges=False, fontsize=4)
    add_box(ax_strat, 5, 35, 3, 10, 'Lymnaea marls', color='#b9d3e3', draw_edges=False, fontsize=5)
    add_box(ax_strat, 5, 45, 3, 2, 'Eocene Base Clay', color='#e3c88c', draw_edges=False, fontsize=4)
    
    draw_wavy_line(ax_strat, 5, 8, 47)
    ax_strat.text(6.5, 48, 'Hiatus', ha='center', va='center', fontsize=6)
    draw_wavy_line(ax_strat, 5, 8, 49)
    
    add_box(ax_strat, 5, 49, 3, 3, 'Rotliegend', color='#d17d54', draw_edges=False, fontsize=5)

    ax_strat.plot([5, 5], [0, 52], color='black', lw=0.5)
    ax_strat.plot([8, 8], [0, 52], color='black', lw=0.5)
    ax_strat.plot([6.5, 6.5], [18, 24], color='black', lw=0.5)
    ax_strat.plot([6.5, 6.5], [32, 35], color='black', lw=0.5)
    for y_val in [0, 2.58, 15, 18, 24, 25, 26.5, 28, 29, 30.5, 32, 35, 45, 52]:
        ax_strat.plot([5, 8], [y_val, y_val], color='black', lw=0.5)
    ax_strat.plot([6.5, 8], [21, 21], color='black', lw=0.5)
    ax_strat.plot([6.5, 8], [33, 33], color='black', lw=0.5)
    ax_strat.plot([6.5, 8], [34, 34], color='black', lw=0.5)

    # Interpreted Seismic Horizons
    horizons = [
        (2.58, 'JT II Top', '#1b9e77'),  # top of Iffezheim Fm = Quaternary base (top vs base still unsure)
        (15, 'JT I Top', '#d95f02'),
        (18, 'OHY Top', '#7570b3'),
        (21, 'UHY Top', '#e7298a'),
        (24, 'CBS Top', '#66a61e'),
        (26.5, 'BNS Top', '#e6ab02'),
        (30.5, 'RT Top', '#a6761d'),
        (45, 'T Base', 'black'),
    ]
    for age, name, color in horizons:
        ax_strat.plot([8.5, 12.5], [age, age], color=color, lw=1.5)
        ax_strat.text(8.5, age - 0.2, name, va='bottom', ha='left', fontsize=6)
        ax_strat.text(12.5, age - 0.2, f"{age} Ma", va='bottom', ha='right', fontsize=6)

        # RIGHT AXIS: SEISMIC SECTION
    segy_file = r'..\segy\new\representative_reflector_2D.segy'
    try:
        with segyio.open(segy_file, 'r', ignore_geometry=True) as f:
            data = f.trace.raw[:]
            
        # Only plot traces 230 to 330
        data_sliced = data[230:330, :]
        
        custom_cmap = 'seismic'
        vmin, vmax = -15, 15
        depth_per_sample = 6 / 1000  # 6m = 0.006 km
        
        # Calculate max depth using the original shape so it's correct
        max_depth = data.shape[1] * depth_per_sample # positive depth
        
        # Plot seismic (transposed so traces are X and depth is Y)
        ax_seis.imshow(data_sliced.T, cmap=custom_cmap, aspect='auto', vmin=vmin, vmax=vmax, extent=[230, 330, max_depth, 0])
        ax_seis.text(0.5, 1.02, "Representative Seismic Section", transform=ax_seis.transAxes, ha='center', va='bottom', fontsize=6, fontweight='bold')
        ax_seis.set_ylabel("Depth (km)", fontsize=6)
        ax_seis.set_xlabel("Traces", fontsize=6)
        ax_seis.tick_params(axis='both', which='major', labelsize=5)
        ax_seis.set_ylim(3.3, 0)
        
    except Exception as e:
        ax_seis.text(0.5, 0.5, f"Could not load SEGY:\n{e}", ha='center', va='center')
        ax_seis.axis('off')

    plt.tight_layout()
    plt.savefig('Figure_2.png', dpi=300, bbox_inches='tight')
    plt.savefig('Figure_2.svg', bbox_inches='tight')
    print("Plot saved to Figure_2.png and .svg")

if __name__ == "__main__":
    main()
