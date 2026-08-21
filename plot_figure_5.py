"""
Generate thickness maps from horizon shapefiles and overlay fault polygons.
interpolates contour data to grids, calculates difference, and plots.
"""
import numpy as np
import shapefile # pyshp
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import os

# Configuration
INPUT_DIR = r"Data"
OUTPUT_DIR = r"Figures"
DEFAULT_RES = 50.0  # Grid resolution in meters

# Define Units (Top Filename, Base Filename, Fault Shapefile Name)
UNITS = [
    ("01_Top_UntereHydrobienschichten.shp", "02_Top_Corbiculaschichten.shp", "Faults_Unit_01_UntereHydrobienschichten.shp"),
    ("02_Top_Corbiculaschichten.shp", "03_Top_BunteNiederroedenerschichten.shp", "Faults_Unit_02_Corbiculaschichten.shp"),
    ("03_Top_BunteNiederroedenerschichten.shp", "04_Top_OberePechelbronnerschichten.shp", "Faults_Unit_03_BunteNiederroedenerschichten.shp"),
    ("04_Top_OberePechelbronnerschichten.shp", "05_Top_Lymnaeenmergel.shp", "Faults_Unit_04_OberePechelbronnerschichten.shp"),
    ("05_Top_Lymnaeenmergel.shp", "06_Basis_Tertiaer.shp", "Faults_Unit_05_Lymnaeenmergel.shp"),
    ("06_Basis_Tertiaer.shp", "07_Top_Muschelkalk.shp", "Faults_Unit_06_TertiaerBasis_Mesozoikum.shp"),
    ("07_Top_Muschelkalk.shp", "08_Top_Buntsandstein.shp", "Faults_Unit_07_Muschelkalk.shp"),
    ("08_Top_Buntsandstein.shp", "09_Basis_Buntsandstein.shp", "Faults_Unit_08_Buntsandstein.shp"),
    ("09_Basis_Buntsandstein.shp", "10_Basement.shp", "Faults_Unit_09_BaseBuntsandstein.shp"),
]

def read_shape_points(filepath):
    """Read X,Y,Z points from POLYLINEZ/POINTZ shapefile."""
    points = []
    try:
        r = shapefile.Reader(filepath)
        for shape in r.shapes():
            # For PolyLineZ, points are in shape.points, Z in shape.z
            # shape.points is list of [x,y]
            # shape.z is list of z values
            if hasattr(shape, 'z') and len(shape.points) == len(shape.z):
                pts = np.array(shape.points)
                zs = np.array(shape.z)
                # Combine to [x,y,z]
                xyz = np.column_stack([pts, zs])
                points.append(xyz)
            elif hasattr(shape, 'points'): # Fallback if Z missing or different length (shouldn't happen for valid Z type)
                 # Check if points have 3 dimensions? No, pyshp separates Z.
                 pass
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
    
    if not points:
        return None
    return np.vstack(points)

def read_polygons(filepath):
    """Read polygons for plotting."""
    polys = []
    try:
        r = shapefile.Reader(filepath)
        for shape in r.shapes():
            if shape.shapeType == shapefile.POLYGON:
                 polys.append(np.array(shape.points))
    except Exception as e:
        print(f"Warning: Could not read faults {filepath}: {e}")
    return polys

def create_grid(points, res=DEFAULT_RES):
    """Create grid coordinates."""
    x_min, x_max = points[:,0].min(), points[:,0].max()
    y_min, y_max = points[:,1].min(), points[:,1].max()
    
    # Add buffer
    buff = res * 5
    xi = np.arange(x_min - buff, x_max + buff, res)
    yi = np.arange(y_min - buff, y_max + buff, res)
    
    Xi, Yi = np.meshgrid(xi, yi)
    return Xi, Yi

def process_unit(top_file, base_file, fault_file, out_dir):
    unit_name = fault_file.replace("Faults_", "").replace(".shp", "")
    print(f"\nProcessing {unit_name}...")
    
    # Paths
    top_path = os.path.join(INPUT_DIR, top_file)
    base_path = os.path.join(INPUT_DIR, base_file)
    fault_path = os.path.join(INPUT_DIR, fault_file) # Faults are in Thicknessmaps too now
    
    # 1. Read Horizon Points
    p_top = read_shape_points(top_path)
    if p_top is None: return
    p_base = read_shape_points(base_path)
    if p_base is None: return
    
    # 2. Downsample if needed (simple skip)
    # If > 200k points, might be slow.
    if len(p_top) > 500000: p_top = p_top[::10]
    elif len(p_top) > 100000: p_top = p_top[::5]
    
    if len(p_base) > 500000: p_base = p_base[::10]
    elif len(p_base) > 100000: p_base = p_base[::5]
    
    # 3. Create Grid based on combined extent
    combined = np.vstack([p_top, p_base])
    Xi, Yi = create_grid(combined)
    print(f"  Grid size: {Xi.shape}")
    
    # 4. Interpolate
    print("  Interpolating Top...")
    Zi_top = griddata(p_top[:,:2], p_top[:,2], (Xi, Yi), method='linear')
    
    print("  Interpolating Base...")
    Zi_base = griddata(p_base[:,:2], p_base[:,2], (Xi, Yi), method='linear')
    
    # 5. Calculate Thickness
    # Z is likely depth (negative or positive). Distance is absolute difference.
    Thickness = np.abs(Zi_top - Zi_base)
    
    # Mask where only one surface exists (nan in either)
    Thickness = np.ma.masked_invalid(Thickness)
    
    # 6. Plot
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Map
    # Use robust range for colors (2-98 percentile) to avoid outliers
    valid_thick = Thickness.compressed()
    if len(valid_thick) == 0:
        print("  No overlapping data for thickness.")
        plt.close()
        return
        
    vmin = np.percentile(valid_thick, 2)
    vmax = np.percentile(valid_thick, 98)
    
    # Main plot
    im = ax.imshow(Thickness, origin='lower', extent=[Xi.min(), Xi.max(), Yi.min(), Yi.max()],
                   cmap='viridis', vmin=vmin, vmax=vmax, alpha=0.9) # Isopach map
    
    cbar = plt.colorbar(im, ax=ax, label='Thickness (m)', pad=0.02)
    
    # Contours (optional, for legibility)
    # ax.contour(Xi, Yi, Thickness, colors='white', alpha=0.3, linewidths=0.5)
    
    # 7. Overlay Faults
    polys = read_polygons(fault_path)
    print(f"  Overlaying {len(polys)} faults...")
    
    from matplotlib.collections import PolyCollection
    if polys:
        pc = PolyCollection(polys, edgecolors='black', facecolors='none', linewidths=1.0, zorder=10)
        ax.add_collection(pc)
        # Add hatch or fill for emphasis? "Overlay" usually implies just showing them.
        # User defined polygons as heave/gap. Filled might be nice.
        pc_fill = PolyCollection(polys, facecolors='white', alpha=0.4, zorder=9)
        ax.add_collection(pc_fill)
    
    # Formatting
    ax.set_title(f'Thickness Map: {unit_name}\n(with Fault Overlay)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Easting')
    ax.set_ylabel('Northing')
    ax.grid(False)
    
    # Save
    out_name = f"ThicknessMap_{unit_name}.png"
    plt.savefig(os.path.join(out_dir, out_name), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_name}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    for top, base, fault in UNITS:
        try:
            process_unit(top, base, fault, OUTPUT_DIR)
        except Exception as e:
            print(f"Failed to process {fault}: {e}")

if __name__ == "__main__":
    main()
