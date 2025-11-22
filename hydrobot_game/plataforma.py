import pygame
from typing import cast
from sprite_base import SpriteConMascara
from rutas import ruta_recurso

RUTA_PLATAFORMA = ruta_recurso("texturas", "obj_ecn", "plataforma.png")


class Plataforma(SpriteConMascara):
    REDUCCION_SUPERIOR = 16

    def __init__(self, posicion: tuple[int, int], *grupos: pygame.sprite.AbstractGroup) -> None:
        super().__init__(*grupos)
        self.imagen_original = pygame.image.load(RUTA_PLATAFORMA).convert_alpha()
        ancho_escalado = int(self.imagen_original.get_width() * 7)
        alto_escalado = int(self.imagen_original.get_height() * 7)
        self.image = pygame.transform.scale(self.imagen_original, (ancho_escalado, alto_escalado))
        self.rect: pygame.Rect = self.image.get_rect(topleft=posicion)
        self.mascara = pygame.mask.from_surface(self.image)
        self._reducir_mascara_superior(self.REDUCCION_SUPERIOR)
        self.posicion = pygame.math.Vector2(posicion)

    def _reducir_mascara_superior(self, reduccion: int) -> None:
        if reduccion <= 0:
            return
        ancho, alto = self.mascara.get_size()
        if ancho == 0 or alto == 0:
            return
        rectangulos = cast(list[pygame.Rect], list(self.mascara.get_bounding_rects()))
        if not rectangulos:
            return
        recta_colision = rectangulos[0].copy()
        for recta in rectangulos[1:]:
            recta_colision.union_ip(recta)
        if recta_colision.height == 0:
            return
        limite_superior = min(recta_colision.top + reduccion, recta_colision.bottom)
        for posicion_y in range(recta_colision.top, limite_superior):
            for posicion_x in range(recta_colision.left, recta_colision.right):
                self.mascara.set_at((posicion_x, posicion_y), 0)
