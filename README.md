# NURG Fault Analysis

This repository contains the Python scripts and processed data used for the multiscale fault analysis in the northern Upper Rhine Graben.

## Repository Structure

- `Data/`: Contains both fault displacement data and the raw seismic interpretations.
  - `1A.xlsx` to `2B.xlsx`: Processed fault displacement data.
  - `all_faults_combined_noqb.csv`: Combined fault metrics.
  - `Faults.zip`: Seismic interpretation data for fault geometries.
  - `Pointset.zip`: Pointset data for interpreted seismic horizons.
  - `Shapefile.zip`: Delineates the area of interest and the limit of the 3D seismic data.
  - `Tsurf.zip`: Tsurf (triangulated surface) data for 3D seismic horizons.
- `fai_analysis/`: Core Python package for data processing and visualization.
- `manual_paths/`: Configuration files for manual point exclusions.
- `plot_figure_2.py`: Script to generate Figure 2 (Stratigraphy).
- `plot_figure_3.py`: Script to generate Figure 3 (Seismic Sections).
- `plot_figure_5.py` / `plot_figure_5_masked.py`: Scripts for Figure 5 (Thickness Maps).
- `plot_figure_6_and_7.py`: Main script to generate Figure 6 (Displacement Profiles) and Figure 7 (EI Comparison).

## Requirements

The analysis requires Python 3.8+ and the following packages:
- `pandas`
- `matplotlib`
- `openpyxl`
- `segyio`

## Usage

To generate the fault displacement and EI comparison plots:
```bash
python plot_figure_6_and_7.py
```

To generate the other figures (make sure required data paths exist):
```bash
python plot_figure_2.py
python plot_figure_3.py
python plot_figure_5.py
```

Results will be saved in the `analysis_output/` and `Figures/` directories, or the local directory depending on the script.

## License
Provided for scientific reproducibility in conjunction with the associated manuscript.
