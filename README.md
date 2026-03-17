# NURG Fault Analysis

This repository contains the Python scripts and processed data used for the multiscale fault analysis in the northern Upper Rhine Graben.

## Repository Structure

- `Data/`: Processed fault displacement data (Excel) and combined metrics (CSV).
- `fai_analysis/`: Core Python package for data processing and visualization.
- `manual_paths/`: Configuration files for manual point exclusions.
- `create_fai_and_throw_plots.py`: Main script to generate Figure 5 (EI Comparison) and Figure 6 (Displacement Profiles).

## Requirements

The analysis requires Python 3.8+ and the following packages:
- `pandas`
- `matplotlib`
- `openpyxl`


## Usage

To generate all plots and metrics:
```bash
python create_fai_and_throw_plots.py
```

Results will be saved in the `analysis_output/` directory.

## License
Provided for scientific reproducibility in conjunction with the associated manuscript.
