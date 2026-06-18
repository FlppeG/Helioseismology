# HelioResearch

This project is dedicated to the study of solar oscillations using **SunPy** and **ds9**. The analyzed data originates from the SDO (Solar Dynamics Observatory) satellite.

## Project Structure

```text
├── data/               # Raw FITS data (excluded from the repository)
├── notebooks/          # Jupyter Notebooks for exploratory data analysis
├── src/                # Python scripts
│   ├── utils/          # Reusable functions and tools
│   └── dev/            # Scripts currently under development
├── .gitignore          # Configuration to exclude data and environments
├── requirements.txt    # Project dependencies
└── README.md
```

## Requirements

Since this project is primarily based on [SunPy](https://docs.sunpy.org/en/stable/tutorial/installation.html), we recommend using **Python 3.11** for optimal performance. It is also strongly recommended to work within a virtual environment (such as Conda or venv). 

## Installation

1. Clone this repository:

```Bash
git clone https://github.com/FlppeG/HelioResearch
   cd helioresearch
```

2. Create and activate a virtual environment:

```Bash
# On Windows:
   python -m venv venv
   .\venv\Scripts\activate

# On Mac/Linux:
   python -m venv venv
   source venv/bin/activate
```

3. Install the dependencies:

```Bash
pip install -r requirements.txt
```

## Data management

The data for analysis consists of **FITS** (Flexible Image Transport System). These can be obtainded from the [JSOC Website](http://jsoc.stanford.edu/ajax/lookdata.html) or by using the `Fido.search` utility included in the `src/` directory.
