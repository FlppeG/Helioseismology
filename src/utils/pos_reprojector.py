import argparse
import astropy.units as u
import sunpy.map
from hpxy2lonlat import hpxy2lonlat
from astropy.io import fits
from pathlib import Path
import concurrent.futures
import warnings
from astropy.wcs import FITSFixedWarning
from cuber import cuber 

"""
Code structure:
---------------
1. Configuration: Suppress warnings related to non-standard FITS headers.
2. process_single_frame: Function to handle the reprojection of a single FITS file.
3. pos_reprojector: Main controller that sets up the target projection (Postel/ARC)
   and manages the parallelized processing of all frames.
4. Main Execution: CLI argument parsing and initialization.

Parameters:
-----------
--dir : str, path
    The directory containing the raw solar data files.
--hpx, --hpy : float
    Helioprojective coordinates (arcsec) of the target flare center.
--res : int
    Spatial resolution (number of pixels) for the output square images.
"""

# Suppress AstroPy warnings for FITS header standard compliance
warnings.filterwarnings('ignore', category=FITSFixedWarning)

def process_single_frame(input_path, output_path, base_header):
    """
    Reprojects a single solar map into the defined target geometry.
    """
    try:
        m = sunpy.map.Map(input_path)
        
        # Update specific observation metadata in the header
        frame_header = base_header.copy()
        frame_header['DATE-OBS'] = m.date.iso.replace(' ', 'T')
        frame_header['DSUN_OBS'] = m.dsun.to(u.m).value

        # Perform reprojection using cubic interpolation (order=3) for high fidelity
        reprojected = m.reproject_to(frame_header, order=3)
        reprojected.save(output_path, overwrite=True)
        return f"Success: {output_path.name}"
    except Exception as e:
        return f"Error in {input_path.name}: {str(e)}"

def pos_reprojector(data_dir, hpx_flare, hpy_flare, n_pix=100, pixel_scale=0.5):
    """
    Coordinates the reprojection pipeline. Finds files, calculates the center,
    defines the Postel/ARC coordinate system, and executes processing in parallel.
    """
    data_path = Path(data_dir)
    # Collect all FITS files, excluding already processed ones
    fits_files = sorted(list(data_path.glob('*.fits')))
    fits_files = [f for f in fits_files if not f.name.startswith('proc_') and 'cube3d' not in f.name]
    
    if not fits_files:
        print(f"Error: No FITS files found in {data_dir}")
        return

    print(f"Reprojecting: {len(fits_files)} files")

    # Use the first map to calculate the central heliographic coordinates of the target
    ref_map = sunpy.map.Map(fits_files[0])
    target_lon, target_lat = hpxy2lonlat(ref_map, hpx_flare, hpy_flare)
    print(f"Center at: Lon={target_lon.value:.2f}, Lat={target_lat.value:.2f}")

    # Build the Target Header (WCS) for Postel (ARC) projection
    # Postel/ARC projection preserves distances from the center, ideal for local helioseismology
    base_header = fits.Header()
    base_header['HGLN_OBS'] = 0.0                                    
    base_header['HGLT_OBS'] = ref_map.meta.get('crlt_obs', 0.0)      
    base_header['CRLN_OBS'] = ref_map.meta.get('crln_obs', 0.0)      
    base_header['CRLT_OBS'] = ref_map.meta.get('crlt_obs', 0.0)      
    base_header['NAXIS'] = 2                                         
    base_header['NAXIS1'] = n_pix                                    
    base_header['NAXIS2'] = n_pix                                    
    base_header['CUNIT1'] = 'arcsec'                                    
    base_header['CUNIT2'] = 'arcsec'
    base_header['CTYPE1'] = 'HGLN-ARC'                               
    base_header['CTYPE2'] = 'HGLT-ARC'                               
    base_header['CRVAL1'] = target_lon.to(u.deg).value
    base_header['CRVAL2'] = target_lat.to(u.deg).value
    base_header['CDELT1'] = pixel_scale
    base_header['CDELT2'] = pixel_scale
    base_header['CRPIX1'] = (n_pix + 1) / 2
    base_header['CRPIX2'] = (n_pix + 1) / 2
    base_header['RSUN_OBS'] = ref_map.rsun_obs.to(u.arcsec).value    
    
    # Execution: Use ProcessPoolExecutor to handle files in parallel
    print("\n Initializing reprojection...")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for f_path in fits_files:
            out_path = data_path / f"proc_{f_path.name}"
            # Submit task to the worker pool
            futures.append(executor.submit(process_single_frame, f_path, out_path, base_header))
            
        # Monitor progress as files complete
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

    print("Finished.")

if __name__ == '__main__':
    # Parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='../../data', help="Raw data directory.")
    parser.add_argument('--hpx', type=float, required=True, help="Helioprojective X (arcsec)")
    parser.add_argument('--hpy', type=float, required=True, help="Helioprojective Y (arcsec)")
    parser.add_argument('--res', type=int, default=100, help="Resolution/Cutout size in pixels")
    args = parser.parse_args()
    
    # Convert inputs to Astropy units
    hpx_flare = args.hpx * u.arcsec
    hpy_flare = args.hpy * u.arcsec

    # Start pipeline
    pos_reprojector(args.dir, hpx_flare, hpy_flare, n_pix=args.res)