from typing import TypedDict

from rutas import ruta_recurso


class ConfiguracionEscena(TypedDict):
    color_fondo: tuple[int, int, int]
    color_suelo: tuple[int, int, int]
    altura_suelo: int


TAMANO_VENTANA: tuple[int, int] = (700, 700)
RUTA_MUSICA_MENU = ruta_recurso("sonido", "musica", "menu.mp3")
RUTA_MUSICA_ESCENA1 = ruta_recurso("sonido", "musica", "ecn1.mp3")
RUTA_MUSICA_ESCENA2 = ruta_recurso("sonido", "musica", "ecn2.mp3")
RUTA_MUSICA_ESCENA3 = ruta_recurso("sonido", "musica", "ecn3.mp3")
RUTA_SONIDO_FELICIDADES = ruta_recurso("sonido", "efectos", "felicidades.mp3")
RUTA_FONDO_MOSAICO = ruta_recurso("texturas", "fondo", "fondo.png")
RUTA_MAPEADO_ESCENA1 = ruta_recurso("texturas", "mapeado", "mapeado1.png")
RUTA_MAPEADO_ESCENA2 = ruta_recurso("texturas", "mapeado", "mapeado2.png")
RUTA_MAPEADO_ESCENA3 = ruta_recurso("texturas", "mapeado", "mapeado3.png")
RUTA_MAPEADO_TUTORIAL = ruta_recurso("texturas", "mapeado", "mapeadot.png")
RUTA_BOTON_MENU = ruta_recurso("texturas", "menu", "boton_menu.png")
RUTA_NPC_TUTORIAL = ruta_recurso("texturas", "personajes", "biopchito.png")

CONFIGURACIONES_ESCENA: dict[str, ConfiguracionEscena] = {
    "1": {"color_fondo": (20, 22, 36), "color_suelo": (60, 120, 80), "altura_suelo": 40},
    "2": {"color_fondo": (32, 20, 46), "color_suelo": (90, 60, 120), "altura_suelo": 60},
    "3": {"color_fondo": (12, 35, 52), "color_suelo": (50, 140, 160), "altura_suelo": 50},
}

CONFIGURACION_TUTORIAL: ConfiguracionEscena = {
    "color_fondo": (15, 30, 25),
    "color_suelo": (120, 90, 40),
    "altura_suelo": 70,
}
