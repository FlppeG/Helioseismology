#!/usr/bin/env python
'''
    Usage: xy2lonlat.py REF_FILE[FITS] hpx hpy

    Returns: (CRLN, CRLT)
'''


def hpxy2lonlat(map_input, hpx, hpy):
    '''
    Converts a coordinate pair from helioprojective to Heliographic Carrington
    '''
    from sunpy.coordinates import frames
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    import warnings
    import logging

    logging.getLogger("sunpy").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", module="sunpy")

    # 1. Aseguramos que hpx y hpy tengan unidades de arcosegundos si vienen como floats
    if not isinstance(hpx, u.Quantity):
        hpx = hpx * u.arcsec
    if not isinstance(hpy, u.Quantity):
        hpy = hpy * u.arcsec

    # 2. Creamos la coordenada usando el frame nativo del mapa FITS
    # Esto hereda automáticamente el rsun, dsun, obstime y observer correctos.
    c = SkyCoord(hpx, hpy, frame=map_input.coordinate_frame)

    # 3. Transformamos a Heliográfica Carrington
    # Nota: Usamos c.carrington para asegurar la transformación directa al frame dinámico
    try:
        carrington_coord = c.transform_to(frames.HeliographicCarrington(observer=map_input.observer_coordinate))
        lon = carrington_coord.lon
        lat = carrington_coord.lat
    except Exception:
        # Alternativa estándar si el observer ya está implícito en el mapeo de transformaciones
        lon = c.heliographic_carrington.lon
        lat = c.heliographic_carrington.lat

    return lon, lat


# ---------------------------------------------------------------------------
# End of code
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    import argparse

    # Bash checks
    def parse_args():
        parser = argparse.ArgumentParser(
            description=('Convert helioprojective x/y to Carrington longitude'
                         '/latitude.')
        )

        parser.add_argument(
            'input_fits',
            help='Input FITS file'
        )

        parser.add_argument(
            'hpx',
            type=float,
            help='Helioprojective X coordinate (arcsec)'
        )

        parser.add_argument(
            'hpy',
            type=float,
            help='Helioprojective Y coordinate (arcsec)'
        )

        return parser.parse_args()

    args = parse_args()

    # ------------------------------------------------------------------

    # Check if file exists
    import os
    import sys
    if not os.path.exists(args.input_fits):
        sys.exit(f'File "{args.input_fits}" does not exist.')

    # ------------------------------------------------------------------

    from sunpy.map import Map

    # Load map
    map_input = Map(args.input_fits)

    # Convert HP x/y to Carrington lon/lat
    crln, crlt = hpxy2lonlat(map_input, args.hpx, args.hpy)

    print(crln.value, crlt.value)