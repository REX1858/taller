import pygame
import random
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from plataforma import Plataforma
from tuberia import Tuberia
from rutas import ruta_recurso

if TYPE_CHECKING:
    from gestor_sonido import GestorSonido


def generar_nivel_desde_imagen(
    ruta_imagen: str,
    tamano_tile: int = 32,
    ancho_pantalla: int = 960,
    minimo_rotas: int = 0,
    prob_rotura: float = 0.1,
    gestor_sonido: Optional["GestorSonido"] = None,
) -> tuple[pygame.sprite.Group, pygame.sprite.Group, int, int, int, dict[str, object]]:
    grupo_plataformas = pygame.sprite.Group()
    grupo_tuberias = pygame.sprite.Group()
    tuberias_verticales: list[Tuberia] = []
    datos_extra: dict[str, object] = {"recta_meta": None, "tuberias_verticales": tuberias_verticales}
    nombre_mapa = Path(ruta_imagen).name.lower()
    es_tutorial = "mapeadot" in nombre_mapa or "tutorial" in nombre_mapa
    
    try:
        imagen_mapa = pygame.image.load(ruta_imagen).convert()
    except pygame.error:
        return grupo_plataformas, grupo_tuberias, 0, 0, 0, datos_extra
    
    ancho_mapa = imagen_mapa.get_width()
    alto_mapa = imagen_mapa.get_height()
    
    ancho_mundo = ancho_mapa * tamano_tile
    desplazamiento_x = (ancho_pantalla - ancho_mundo) // 2
    if desplazamiento_x < 0:
        desplazamiento_x = 0
    
    COLOR_PLATAFORMA = (0, 0, 0)
    COLOR_TUBERIA_NORMAL = (0, 255, 0)
    COLOR_TUBERIA_DANABLE = (255, 0, 0)
    COLOR_TUBERIA_AZUL = (0, 0, 255)
    COLOR_TUBERIA_TUTORIAL = (255, 255, 0)
    COLOR_META_TUTORIAL = (0, 255, 255)
    COLOR_VACIO = (255, 255, 255)

    ruta_tuberia_h = ruta_recurso("texturas", "obj_ecn", "tuberia_h.png")
    ruta_tuberia_h1 = ruta_recurso("texturas", "obj_ecn", "tuberia_h1.png")
    ruta_tuberia_h_1 = ruta_recurso("texturas", "obj_ecn", "tuberia_h-1.png")
    
    for y in range(alto_mapa):
        for x in range(ancho_mapa):
            color = imagen_mapa.get_at((x, y))[:3]
            
            if color == COLOR_VACIO:
                continue
            
            posicion = (x * tamano_tile + desplazamiento_x, y * tamano_tile)
            
            if color == COLOR_PLATAFORMA:
                Plataforma(posicion, grupo_plataformas)
            elif color == COLOR_TUBERIA_NORMAL:
                Tuberia(posicion, False, gestor_sonido, grupo_tuberias, ruta_imagen=ruta_tuberia_h)
            elif color == COLOR_TUBERIA_DANABLE:
                danada = True if es_tutorial else random.random() < prob_rotura
                Tuberia(posicion, danada, gestor_sonido, grupo_tuberias, ruta_imagen=ruta_tuberia_h)
            elif color == COLOR_TUBERIA_AZUL:
                colores_conexion = (COLOR_TUBERIA_DANABLE, COLOR_TUBERIA_NORMAL)
                conexion_izquierda = False
                conexion_derecha = False
                if x - 1 >= 0:
                    color_izq = imagen_mapa.get_at((x - 1, y))[:3]
                    conexion_izquierda = color_izq in colores_conexion
                if x + 1 < ancho_mapa:
                    color_der = imagen_mapa.get_at((x + 1, y))[:3]
                    conexion_derecha = color_der in colores_conexion
                ruta_elegida = ruta_tuberia_h
                if conexion_derecha:
                    ruta_elegida = ruta_tuberia_h_1
                elif conexion_izquierda:
                    ruta_elegida = ruta_tuberia_h1
                danada = random.random() < prob_rotura
                Tuberia(posicion, danada, gestor_sonido, grupo_tuberias, ruta_imagen=ruta_elegida)
            elif color == COLOR_TUBERIA_TUTORIAL:
                tuberia_tutorial = Tuberia(posicion, False, gestor_sonido, grupo_tuberias, ruta_imagen=ruta_tuberia_h)
                setattr(tuberia_tutorial, "orientacion", "vertical")
                setattr(tuberia_tutorial, "requiere_caida", True)
                setattr(tuberia_tutorial, "es_tutorial", True)
                tuberias_verticales.append(tuberia_tutorial)
            elif color == COLOR_META_TUTORIAL:
                datos_extra["recta_meta"] = pygame.Rect(posicion[0], posicion[1], tamano_tile, tamano_tile)
    
    altura_mundo = alto_mapa * tamano_tile
    if minimo_rotas > 0:
        tuberias_lista = [t for t in grupo_tuberias if not getattr(t, "es_tutorial", False)]
        actuales_rotas = [t for t in tuberias_lista if getattr(t, "danada", False)]
        faltan = max(0, minimo_rotas - len(actuales_rotas))
        if faltan > 0:
            candidatas = [t for t in tuberias_lista if not getattr(t, "danada", False)]
            random.shuffle(candidatas)
            for t in candidatas[:faltan]:
                setattr(t, "danada", True)
    return grupo_plataformas, grupo_tuberias, altura_mundo, desplazamiento_x, ancho_mundo, datos_extra
