"""
Coordinate Transformation Utility: Helioprojective to Heliographic Carrington
----------------------------------------------------------------------------
This script provides a utility to convert solar coordinate pairs (x, y) 
from the instrument frame (Helioprojective) to the Carrington solar surface 
coordinate system, accounting for observation time and satellite position.

Code structure:
---------------
1. hpxy2lonlat: Core function that handles the coordinate system math.
2. Main Execution: CLI argument parsing and file processing logic.

Usage:
------
python xy2lonlat.py <fits_file> <hpx> <hpy>
"""

import argparse
import logging
import warnings
import os
import sys
from sunpy.map import Map
from sunpy.coordinates import frames
import astropy.units as u
from astropy.coordinates import SkyCoord

def hpxy2lonlat(map_input, hpx, hpy):
    """
    Converts a coordinate pair from Helioprojective (sensor space) 
    to Heliographic Carrington (solar surface space).
    """
    # Suppress SunPy/Astropy noise during transformation
    logging.getLogger("sunpy").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", module="sunpy")

    # 1. Normalize units: Ensure inputs are treated as arcseconds
    if not isinstance(hpx, u.Quantity):
        hpx = hpx * u.arcsec
    if not isinstance(hpy, u.Quantity):
        hpy = hpy * u.arcsec

    # 2. Create SkyCoord object using the FITS map native frame
    # This inherits the observation time, satellite distance, and P-angle
    c = SkyCoord(hpx, hpy, frame=map_input.coordinate_frame)

    # 3. Transform to Heliographic Carrington
    # We define the observer from the map metadata to perform the transformation
    try:
        carrington_coord = c.transform_to(frames.HeliographicCarrington(observer=map_input.observer_coordinate))
        lon = carrington_coord.lon
        lat = carrington_coord.lat
    except Exception:
        # Fallback method if specific observer object is unavailable
        lon = c.heliographic_carrington.lon
        lat = c.heliographic_carrington.lat

    return lon, lat


if __name__ == '__main__':
    # CLI argument parsing
    def parse_args():
        parser = argparse.ArgumentParser(
            description='Convert helioprojective x/y to Carrington longitude/latitude.'
        )
        parser.add_argument('input_fits', help='Input FITS file path')
        parser.add_argument('hpx', type=float, help='Helioprojective X coordinate (arcsec)')
        parser.add_argument('hpy', type=float, help='Helioprojective Y coordinate (arcsec)')
        return parser.parse_args()

    args = parse_args()

    # Verify file existence before processing
    if not os.path.exists(args.input_fits):
        sys.exit(f'Error: File "{args.input_fits}" does not exist.')

    # Load FITS data into a SunPy Map
    map_input = Map(args.input_fits)

    # Execute transformation
    crln, crlt = hpxy2lonlat(map_input, args.hpx, args.hpy)

    # Output result to stdout
    print(crln.value, crlt.value)