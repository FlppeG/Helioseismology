from sunpy.net import Fido, attrs as a
from astropy.coordinates import SkyCoord
from sunpy.net import jsoc
import astropy.units as u
import os

# Time interval  # Flare onset at 2022-05-10 13:55:00 UT
time_0 = '2022-05-10T13:24:00'
time_1 = '2022-05-10T14:55:00'

# 1. Definimos el centro del recorte (Coordenadas Helioproyectivas)
centro_region = SkyCoord(-300 * u.arcsec, 200 * u.arcsec, frame='helioprojective', observer='earth')

# 2. Definimos el tamaño de la caja (ej. 400x400 arcosegundos es un buen tamaño para una mancha solar)
ancho = 400 * u.arcsec
alto = 400 * u.arcsec

# Register email in JSOC at:
# http://jsoc.stanford.edu/ajax/register_email.html
email = 'lfelipelosadag@gmail.com'

out_dir = './data'
series = 'hmi.v_45s'  # LOS Doppler
# Other series are:
#       series = 'hmi.ic_45s'         # Continuum intensity (HMI)
#       series = 'hmi.m_45s'          # LOS Magnetic field (HMI)
#       series = 'aia.lev1_euv_12s'   # EUV data (AIA)
#       series = 'aia.lev1_uv_24s'    # UV data (AIA)
# wavelength = 171  # Only for AIA observations

cadence = 45*u.s   # Cadence of data (45 s for HMI, 12/24 s for AIA)

# Make output directory
os.makedirs(out_dir, exist_ok=True)


def download_data():
    # Select data to download: HMI example
    result = Fido.search(
        a.Time(time_0, time_1),
        a.jsoc.Series(series),
        a.jsoc.Notify(email),
        a.Sample(cadence),
        # a.Wavelength(wavelength*u.angstrom)  # Only for AIA observations
        jsoc.Segment({
        'hop': True,                       # 'hop' le dice al JSOC que haga el recorte en el servidor
        'tracking': True,                  # El Sol rota; esto hace que la caja "siga" a la mancha y no se te salga del cuadro
        'register': True,                  # Alinea y corrige la rotación física del satélite
        'request_type': 'cutout',          # Especifica que es un recorte
        'sizeX': ancho.value,              # Ancho de la caja en arcosegundos
        'sizeY': alto.value,               # Alto de la caja en arcosegundos
        'centerX': centro_region.Tx.value, # Posición X del centro
        'centerY': centro_region.Ty.value  # Posición Y del centro
        })
    )
    num_files = len(result[0])

    # Check if there are any bad files in data
    bad_files = 0
    for i in range(num_files):
        quality = result[0][i]['QUALITY']
        if quality != 0:
            bad_files += 1
    print(f'\n\nNumber of files: {num_files}\nMissing frames: {bad_files}\n')

    print("Iniciando la descarga de la secuencia completa...")

    downloaded_files = Fido.fetch(
        result[0], max_conn=10,
        path=f'{out_dir}/' + '{file}.fz',
        retries=50,               # Parfive reintentará individualmente hasta 50 veces si el servidor falla
    )

# Control de daños extra: por si Stanford se satura y caen conexiones
    if downloaded_files.errors:
        print(f"Se detectaron {len(downloaded_files.errors)} archivos caídos por red. Reintentando remanente...")
        downloaded_files = Fido.fetch(result[0], path=f'{out_dir}/' + '{file}.fz', max_conn=5)

    print("¡Proceso finalizado con éxito!")

    print(f'Number of files donwloaded {downloaded_files}')


download_data()