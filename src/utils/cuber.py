import argparse
import numpy as np
import sunpy.map
from astropy.io import fits
from pathlib import Path
import warnings
from sunpy.util.exceptions import SunpyUserWarning

"""
Code structure:
---------------
1. Configuration: Suppress warnings for inconsistent FITS headers/metadata.
2. cuber: Main logic to aggregate 2D FITS files into a single 3D FITS cube.
   - Handles file selection based on 'cutout' or 'fulldisk' modes.
   - Manages memory efficiently using FITS memmap.
3. Main Execution: CLI argument parsing for automation.

Parameters:
-----------
mode : str
    'cutout' (processes files starting with 'proc_') or 'fulldisk' (processes raw files).
data_dir : str, path
    Source directory containing the 2D FITS images.
output_name : str
    Filename for the generated 3D cube.
output_dir : str, path
    Directory where the final cube will be saved.
"""

# Suppress SunPy warnings regarding metadata dimensions
warnings.filterwarnings('ignore', category=SunpyUserWarning)

def cuber(mode, data_dir, output_name, output_dir=None):
    """
    Combines a series of 2D FITS files into a single 3D FITS cube.
    Uses memory mapping to avoid loading entire image sequences into RAM.
    """
    data_path = Path(data_dir)
    
    if not data_path.is_dir():
        print(f"Error: Data directory '{data_dir}' does not exist.")
        return

    # 1. File Selection logic based on processing mode
    if mode == 'cutout':
        prefix = 'proc_'
        output_name = output_name or 'cutout_cube3d.fits'
        # Select only files that were processed by the reprojector
        files = [f for f in data_path.glob('*.fits') if f.name.startswith(prefix)]
    else: 
        output_name = output_name or 'fulldisk_cube3d.fits'
        # Select raw files, ignoring cubes and already processed files
        files = [f for f in data_path.glob('*.fits') if not f.name.startswith('proc_') and 'cube3d' not in f.name]

    files = sorted(files)

    # 2. Setup output directory structure
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = data_path  # Default to data directory if none specified
        
    out_path.mkdir(parents=True, exist_ok=True)
    final_cube_path = out_path / output_name

    # Safety check: Exclude the output file itself if it exists in the input list
    files = [f for f in files if f.name != final_cube_path.name]

    if not files:
        print(f"Error: No valid FITS files found for mode '{mode}' in: {data_dir}")
        return

    print(f"Found {len(files)} FITS files.")

    # 3. Extract dimensions and metadata from the first valid file
    reference_map = None
    for path in files:
        try:
            m = sunpy.map.Map(path)
            # Ensure we are referencing a 2D map
            if len(m.data.shape) == 2:
                reference_map = m
                break
        except Exception:
            continue
            
    if reference_map is None:
        print("Error: No valid 2D FITS file found for reference.")
        return

    n_y, n_x = reference_map.data.shape
    n_t = len(files) # Number of time frames
    data_type = reference_map.data.dtype

    # Sanitize metadata header
    clean_meta = {}
    for key, value in reference_map.meta.items():
        # Skip nested structures or comments that break FITS standard
        if key.lower() == 'keycomments' or isinstance(value, (dict, list)):
            continue
        clean_meta[key] = value.replace('\n', ' ') if isinstance(value, str) else value

    header = fits.Header(clean_meta)
    
    # Remove 'BLANK' keyword which is not standard for float data arrays
    if 'BLANK' in header:
        del header['BLANK']
        
    # Define 3D WCS dimensions
    header['NAXIS'] = 3
    header['NAXIS1'] = n_x
    header['NAXIS2'] = n_y
    header['NAXIS3'] = n_t
    
    # 4. ALLOCATE: Create the empty FITS file on disk
    print(f"Allocating space in '{final_cube_path.parent.name}' for the cube ({n_t} frames)...")
    empty_data = np.zeros((n_t, n_y, n_x), dtype=data_type)
    
    hdu = fits.PrimaryHDU(data=empty_data, header=header)
    hdu.writeto(final_cube_path, overwrite=True)
    del empty_data # Free RAM immediately

    # 5. FILL: Inject data using memmap for memory efficiency
    print("Starting data injection...")
    valid_layers = 0
    
    with fits.open(final_cube_path, mode='update', memmap=True) as hdul:
        for path in files:
            try:
                m = sunpy.map.Map(path)
                # Verify dimensions match the reference
                if m.data.shape == (n_y, n_x):
                    # Write directly to the memmapped file on disk
                    hdul[0].data[valid_layers, :, :] = m.data
                    valid_layers += 1
            except Exception:
                continue
        hdul.flush() # Ensure all data is physically written to the disk

    print(f"3D Cube successfully saved at: {final_cube_path}")
    print(f"To visualize, run: ds9 {final_cube_path} &")

if __name__ == '__main__':
    # CLI argument parsing
    parser = argparse.ArgumentParser(description="Unify 2D FITS images into a 3D FITS cube.")
    parser.add_argument('mode', choices=['fulldisk', 'cutout'], help="Processing mode")
    parser.add_argument('--dir', default='.', help="Input directory containing FITS files")
    parser.add_argument('--out', default='', help="Output filename")
    parser.add_argument('--out_dir', default='../../cubes', help="Directory to save the resulting cube")
    
    args = parser.parse_args()
    cuber(args.mode, args.dir, args.out, args.out_dir)