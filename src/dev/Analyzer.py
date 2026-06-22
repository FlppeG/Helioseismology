# Ejemplo conceptual para tu nuevo script analyzer.py
import glob
from cuber import cuber

# 1. Empaquetar
print("Generando cubo 3D...")
cuber(mode='cutout', 
      data_dir='../../data', # Asegúrate de que apunte donde están los proc_*.fits
      output_name='postel_cube3d.fits', 
      output_dir='../../cubes')

# 2. FFT (Tu futuro código de heliosismología)
# print("Iniciando FFT...")
# ... aquí iría tu lógica de FFT sobre postel_cube3d.fits