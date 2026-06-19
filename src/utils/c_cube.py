import os
import sunpy.map
import argparse
import astropy.units as u
from astropy.coordinates import SkyCoord
from hpxy2lonlat import hpxy2lonlat
from astropy.io import fits

"""
    Code structure:
    ---------------
    Generate a cutout series of FITS files mapped to a Carrington coordinate grid by
    performing a spatial reprojection. It calculates the center of the cutout with
    hpxy2lonlat and constructs a new WCS header incorporating the retrieved Carrington
    coordinate metadata.

    Parameters:
    -----------
    data_dir :              str   - .fits data route
    hpx_flare, hpy_flare :  float - Helioprojective event coordinates
    n_pix :                 int   - Map resolution (shape)
    pixel_scale :           float - Degrees per pixel
"""

def generate_carrington_cube(data_dir, 
                             hpx_flare, 
                             hpy_flare, 
                             n_pix=100, 
                             pixel_scale=0.1):
    
    # 1. File identification
    fits_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.fits')])
    
    if not fits_files:
        print(f"Error: No FITS files found in {data_dir}")
        return

    # Use the first .fits file for reference
    ref_map = sunpy.map.Map(os.path.join(data_dir, fits_files[0]))
    
    #Carrington coordinate conversion
    target_lon, target_lat = hpxy2lonlat(ref_map, hpx_flare, hpy_flare)
    print(f"Center at: Lon={target_lon.value:.2f}, Lat={target_lat.value:.2f}")

    #New header construction
    header = fits.Header()

    #Time and observer metadata
    header['DATE-OBS'] = ref_map.date.iso.replace(' ', 'T')     # ISO timestamp of the observation (e.g.,'YYYY-MM-DDTHH:MM:SS') with a safety re-assignment.    
    header['HGLN_OBS'] = 0.0                                    # For earth/SDO, the Stonyhurst longitude is 0.
    header['HGLT_OBS'] = ref_map.meta.get('crlt_obs', 0.0)      # Heliographic Latitude of the observer (B0 angle, solar tilt toward Earth).
    header['CRLN_OBS'] = ref_map.meta.get('crln_obs', 0.0)      # Carrington Longitude of the central meridian as seen by the observer (L0 angle).
    header['CRLT_OBS'] = ref_map.meta.get('crlt_obs', 0.0)      # Carrington Latitude of the central meridian (equivalent to HGLT_OBS).
    
    #Image geometry and dimensions of the map
    header['NAXIS'] = 2                                         # 2D spatial image map.
    header['NAXIS1'] = n_pix                                    # Number of pixels along X-axis (width)
    header['NAXIS2'] = n_pix                                    # Number of pixels along Y-axis (Height)

    #WCS definition
    header['CUNIT1'] = 'deg'                                    #Both are angular degrees since we are working with Carrington coordinates.
    header['CUNIT2'] = 'deg'
    
    #CTYPE mapping (-CAR specifies Linear/Cartesian map projection): 
    header['CTYPE1'] = 'CRLN-CAR'                               #CRLN-CAR is Carrington longitude
    header['CTYPE2'] = 'CRLT-CAR'                               #CRLT-CAR is Carrington latitude
    
    #CRVAL: Coordinate values at the reference pixel (the target center)
    header['CRVAL1'] = target_lon.to(u.deg).value
    header['CRVAL2'] = target_lat.to(u.deg).value
    
    #CDELT: Grid resolution/pixel scale (degrees per pixel)
    header['CDELT1'] = pixel_scale
    header['CDELT2'] = pixel_scale
    
    #CRPIX: 1-indexed location of the reference pixel (centered mathematically)
    header['CRPIX1'] = (n_pix + 1) / 2
    header['CRPIX2'] = (n_pix + 1) / 2
    
    #Physical Solar physical constants 
    header['DSUN_OBS'] = ref_map.dsun.to(u.m).value             #Distance from observer to the Sun's center in meters
    header['RSUN_OBS'] = ref_map.rsun_obs.to(u.arcsec).value    #Apparent angular radius of the Sun in arcseconds as seen by SDO
    
    # 4. Reprojection procedure
    print("Initializing series reprojection...")
    for f in fits_files:
        input_path = os.path.join(data_dir, f)
        output_path = os.path.join(data_dir, f'proc_{f}')
        
        #The following lines perform an interpolation and re-griding of the original map onto the target Carrington 
        #coordinate frame specified by the custom WCS header template. By default, this performs a bi-linear interpolation.
        #Finally, it exports the reprojected map back to FITS format, conserving the new Carrington metadata and WCS coordinate system definitions.

        m = sunpy.map.Map(input_path)                           #Load the raw 2D helioprojective map from disk
        reprojected = m.reproject_to(header)
        reprojected.save(output_path, overwrite=True)
        print(f"Saved: {output_path}")

    print("Finished.")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='../../data')
    parser.add_argument('--hpx', type=float, required=True)
    parser.add_argument('--hpy', type=float, required=True)
    parser.add_argument('--res', type=int, default=100)
    args = parser.parse_args()
    
    hpx_flare = args.hpx * u.arcsec
    hpy_flare = args.hpy * u.arcsec

    generate_carrington_cube(args.dir, hpx_flare, hpy_flare, n_pix=args.res)