import os
import subprocess
import astropy.units as u
from sunpy.net import Fido, attrs as a

"""
    Code structure:
    ---------------
    1. Querying data: Search SDO/JSOC data using Fido.search based on time, 
       series, and cadence.
    2. Quality Check: Check the data table to print the total number of frames 
       and detect potential data gaps or corrupted files (QUALITY != 0).
    3. Downloading data: Fetch the raw compressed (.fz) files from JSOC using 
       Fido.fetch with parallel connections.
    4. Decompression: Unpack the downloaded .fz files into standard .fits 
       format using the Rice decompression tool 'funpack'.


    Parameters:
    -----------
    time_0, time_1:     str - Timestamps of the event
    series:             str - Encoding of the data provided by SDO instruments
    out_dir:            str - .fits data route
    email:              str - Registered email at JSOC
    cadence:            str - Cadence of data (45 s for HMI, 12/24 s for AIA)
    About series:
    For default we use series = 'hmi.v_45s', which is the encoding for
    LOS Dopplergrams, but there are other options. Other series are:

       series = 'hmi.ic_45s'         # Continuum intensity (HMI)
       series = 'hmi.m_45s'          # LOS Magnetic field (HMI)
       series = 'aia.lev1_euv_12s'   # EUV data (AIA)
       series = 'aia.lev1_uv_24s'    # UV data (AIA)

        wavelength = 171             # Only for AIA observations
"""

def SDOdownload(time_0, time_1, series, out_dir, email):
    # 1. Full Disk download
    print("Searching data...")
    result = Fido.search(
        a.Time(time_0, time_1),
        a.jsoc.Series(series),                  # LOS Doppler
        a.jsoc.Notify(email),
        a.Sample(cadence),
        # a.Wavelength(wavelength*u.angstrom)   # Only for AIA observations
        )
    
    num_files = len(result[0])

    # Check if there are any bad files in data
    bad_files = 0
    for i in range(num_files):
        quality = result[0][i]['QUALITY']
        if quality != 0:
            bad_files += 1
    print(f'\n\nNumber of files: {num_files}\nMissing frames: {bad_files}\n')

    print("Initializing complete sequence download...")

    #Download data (with retries)
    files = Fido.fetch(result,
                        path=f'{out_dir}/' + '{file}.fz',
                        max_conn=10,
                        retries=50)
    print(f"Finished. {len(files)} archives obtained.")
    
    # 2. Uncompression
    for f in files:
        if f.endswith('.fz'):
            print(f"Uncompressing: {f}")
        subprocess.run(['funpack', f])
        
if __name__ == '__main__':

    #Config
    time_0 = '2026-06-03T11:15:00'          
    time_1 = '2026-06-03T11:50:00'          
    series = 'hmi.v_45s'                    
    email = 'lfelipelosadag@gmail.com'      
    out_dir = '../../data'                  
    cadence = 45*u.s                        
    os.makedirs(out_dir, exist_ok=True)     #Make output directory
    
    SDOdownload(time_0, time_1, series, out_dir, email)
