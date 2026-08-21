"""
Generate masked thickness maps.
Calculates thickness and overlays faults with a buffer to hide interpolation artifacts.
"""
import numpy as np
import shapefile # pyshp
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from shapely.geometry import Polygon
import os

# Configuration
INPUT_DIR = r"Data"
OUTPUT_DIR = r"Figures_Masked"
DEFAULT_RES = 50.0  # Grid resolution in meters
BUFFER_DIST = 100.0 # Buffer distance in meters to mask artifacts

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
    """Read X,Y,Z points."""
    points = []
    try:
        r = shapefile.Reader(filepath)
        for shape in r.shapes():
            if hasattr(shape, 'z') and len(shape.points) == len(shape.z):
                pts = np.array(shape.points)
                zs = np.array(shape.z)
                xyz = np.column_stack([pts, zs])
                points.append(xyz)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
    
    if not points:
        return None
    return np.vstack(points)

def read_buffered_polygons(filepath, buffer_dist=BUFFER_DIST):
    """Read polygons and return buffered Shapely objects + original points."""
    buffered_polys = []
    original_polys = []
    
    try:
        r = shapefile.Reader(filepath)
        for shape in r.shapes():
            if shape.shapeType == shapefile.POLYGON and len(shape.points) > 2:
                # Convert to Shapely
                poly = Polygon(shape.points)
                if poly.is_valid:
                    buffered = poly.buffer(buffer_dist)
                    buffered_polys.append(buffered)
                    original_polys.append(np.array(shape.points))
                else:
                    # Try to fix validity or skip
                    buffered = poly.buffer(0).buffer(buffer_dist)
                    buffered_polys.append(buffered)
                    original_polys.append(np.array(shape.points))
    except Exception as e:
        print(f"Warning: Could not read faults {filepath}: {e}")
        
    return buffered_polys, original_polys

def shapely_to_mpl(shapely_poly):
    """Convert Shapely polygon to list of coordinate arrays for matplotlib."""
    if shapely_poly.is_empty:
        return []
    
    polys = []
    if shapely_poly.geom_type == 'Polygon':
        polys.append(np.array(shapely_poly.exterior.coords))
        # Handle interiors (holes) if needed, but for masking artifacts we mostly care about coverage
        # Actually for masking, filling holes is fine (we want to hide artifacts inside)
    elif shapely_poly.geom_type == 'MultiPolygon':
        for sub_poly in shapely_poly.geoms:
            polys.append(np.array(sub_poly.exterior.coords))
            
    return polys

def create_grid(points, res=DEFAULT_RES):
    """Create grid coordinates."""
    x_min, x_max = points[:,0].min(), points[:,0].max()
    y_min, y_max = points[:,1].min(), points[:,1].max()
    buff = res * 5
    xi = np.arange(x_min - buff, x_max + buff, res)
    yi = np.arange(y_min - buff, y_max + buff, res)
    Xi, Yi = np.meshgrid(xi, yi)
    return Xi, Yi

def process_unit(top_file, base_file, fault_file, out_dir):
    unit_name = fault_file.replace("Faults_", "").replace(".shp", "")
    print(f"\nProcessing {unit_name}...")
    
    top_path = os.path.join(INPUT_DIR, top_file)
    base_path = os.path.join(INPUT_DIR, base_file)
    fault_path = os.path.join(INPUT_DIR, fault_file)
    
    # 1. Read Horizon Points
    p_top = read_shape_points(top_path)
    if p_top is None: return
    p_base = read_shape_points(base_path)
    if p_base is None: return
    
    # Downsample
    if len(p_top) > 500000: p_top = p_top[::10]
    elif len(p_top) > 100000: p_top = p_top[::5]
    
    if len(p_base) > 500000: p_base = p_base[::10]
    elif len(p_base) > 100000: p_base = p_base[::5]
    
    # 2. Grid & Interpolate
    combined = np.vstack([p_top, p_base])
    Xi, Yi = create_grid(combined)
    
    print("  Interpolating...")
    Zi_top = griddata(p_top[:,:2], p_top[:,2], (Xi, Yi), method='linear')
    Zi_base = griddata(p_base[:,:2], p_base[:,2], (Xi, Yi), method='linear')
    
    # 3. Calculate Thickness
    Thickness = np.abs(Zi_top - Zi_base)
    Thickness = np.ma.masked_invalid(Thickness)
    
    # 4. Read Faults & Buffer
    print("  Buffering faults...")
    buffered_polys, original_polys = read_buffered_polygons(fault_path)
    
    # Convert buffered shapely polys to matplotlib format
    mpl_buffered = []
    for bp in buffered_polys:
        mpl_buffered.extend(shapely_to_mpl(bp))
    
    # 5. Plot
    fig, ax = plt.subplots(figsize=(12, 10))
    
    valid_thick = Thickness.compressed()
    if len(valid_thick) == 0:
        plt.close()
        return
        
    vmin = np.percentile(valid_thick, 2)
    vmax = np.percentile(valid_thick, 98)
    
    # Plot Map
    im = ax.imshow(Thickness, origin='lower', extent=[Xi.min(), Xi.max(), Yi.min(), Yi.max()],
                   cmap='jet', vmin=vmin, vmax=vmax, alpha=0.9)
    
    cbar = plt.colorbar(im, ax=ax, label='Thickness (m)', pad=0.02)
    
    from matplotlib.collections import PolyCollection
    
    # Overlay 1: White Mask (Buffered Faults) - to hide artifacts
    if mpl_buffered:
        # Use a white facecolor to "erase" the underlying map
        pc_mask = PolyCollection(mpl_buffered, facecolors='white', edgecolors='white', linewidths=1.0, zorder=15)
        ax.add_collection(pc_mask)
        
    # Overlay 2: Fault Outline (Original) - to show structural location
    if original_polys:
        pc_fault = PolyCollection(original_polys, facecolors='none', edgecolors='black', linewidths=0.5, zorder=20)
        ax.add_collection(pc_fault)
    
    ax.set_title(f'Thickness Map: {unit_name}\n(Masked Faults, {BUFFER_DIST}m Buffer)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Easting')
    ax.set_ylabel('Northing')
    ax.grid(False)
    
    out_name = f"ThicknessMap_{unit_name}_Masked.png"
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
