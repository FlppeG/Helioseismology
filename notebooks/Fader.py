import matplotlib.pyplot as plt
# Importamos la herramienta Slider para añadir controles interactivos a la ventana gráfica
from matplotlib.widgets import Slider

import astropy.units as u

import sunpy.map
# Importamos dos longitudes de onda distintas: 171 Å (Corona a ~1M Kelvin) y 1600 Å (Cromosfera/Transición a ~100,000 Kelvin)
from sunpy.data.sample import AIA_171_IMAGE, AIA_1600_IMAGE

# Creamos los objetos de mapa solar para cada longitud de onda con sus respectivos metadatos
map_171 = sunpy.map.Map(AIA_171_IMAGE)
map_1600 = sunpy.map.Map(AIA_1600_IMAGE)

# Inicializamos la ventana gráfica (Figure)
fig = plt.figure()

# Usamos 'add_axes' en lugar de 'add_subplot' para controlar con precisión milimétrica la posición del mapa solar.
# Los valores [izq, abajo, ancho, alto] están en porcentaje (de 0 a 1). 
# Al dejar 'abajo' en 0.2 (20%), guardamos intencionalmente un espacio vacío debajo de la imagen para colocar el slider.
# Usamos la proyección WCS de map_171 para mantener la consistencia de los ejes en coordenadas físicas.
ax = fig.add_axes([0.1, 0.2, 0.9, 0.7], projection=map_171)

# Dibujamos primero la imagen de 1600 Å de fondo. Se guarda en la variable 'im_1600'.
im_1600 = map_1600.plot(axes=ax)

# Dibujamos encima la imagen de 171 Å ('im_171'). 
# alpha=0.5 hace que inicie con un 50% de transparencia para mezclar visualmente ambos mapas.
# clip_interval=(1, 99.99)*u.percent elimina los píxeles con ruido extremo (oscuros o saturados), realzando los bucles corona.
im_171 = map_171.plot(axes=ax, alpha=0.5, clip_interval=(1, 99.99)*u.percent)

# Ponemos un título descriptivo en la parte superior del gráfico
ax.set_title('AIA 171 + 1600')

# Creamos un eje independiente exclusivo para el Slider en el espacio libre inferior que reservamos antes.
# Su posición es: izquierda 25%, abajo 5%, ancho 65% y una altura muy delgada de solo el 3%.
ax_slider = fig.add_axes([0.25, 0.05, 0.65, 0.03])

# Inicializamos el Slider dentro de sus ejes. Se llamará 'Alpha', irá de un valor mínimo de 0 a un máximo de 1, 
# y su valor inicial por defecto en pantalla será 0.5 (valinit=0.5).
slider = Slider(ax_slider, 'Alpha', 0, 1, valinit=0.5)


# Definimos la función de actualización que Matplotlib llamará automáticamente cada vez que muevas el ratón sobre el slider.
def update(val):
    # Extraemos el valor numérico actual en el que se encuentra detenido el slider
    alpha = slider.val
    # Le aplicamos directamente ese nuevo valor de transparencia a la capa superior (AIA 171)
    im_171.set_alpha(alpha)


# Conectamos el evento 'on_changed' del slider con nuestra función 'update'. 
# Esto crea el bucle interactivo: si el slider se mueve, la transparencia de la imagen cambia inmediatamente.
slider.on_changed(update)

# Desplegamos la ventana interactiva en la pantalla
plt.show()