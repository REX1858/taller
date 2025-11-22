import pygame
from typing import Iterable


_COLOR_FONDO = (18, 24, 36, 200)
_COLOR_BORDE = (90, 110, 150)
_MARGEN = 14
_TAMANO = (200, 150)
_ZOOM_MIN = 0.3
_ZOOM_MAX = 4.0


def _clamp(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(valor, maximo))


def _iterar_grupo(grupo: pygame.sprite.Group | Iterable[pygame.sprite.Sprite] | None) -> Iterable[pygame.sprite.Sprite]:
    if grupo is None:
        return ()
    if isinstance(grupo, pygame.sprite.Group):
        return grupo.sprites()
    return grupo


class MiniMapa:
    """Dibuja un minimapa con texturas reales de los sprites."""

    def __init__(self, tamano: tuple[int, int] = _TAMANO, margen: int = _MARGEN) -> None:
        self.tamano = tamano
        self.margen = margen
        self.superficie = pygame.Surface(self.tamano, pygame.SRCALPHA)
        self.zoom = 1.0
        self.limites: pygame.Rect | None = None
        self._escala_base = 1.0

    def establecer_limites(self, limites: pygame.Rect | None) -> None:
        if limites is None:
            self.limites = None
            self._escala_base = 1.0
            return
        self.limites = limites.copy()
        if limites.width > 0 and limites.height > 0:
            self._escala_base = min(
                self.tamano[0] / limites.width,
                self.tamano[1] / limites.height,
            )
        else:
            self._escala_base = 1.0

    def ajustar_zoom(self, delta: float) -> None:
        self.zoom = _clamp(self.zoom + delta, _ZOOM_MIN, _ZOOM_MAX)

    def dibujar(
        self,
        superficie_destino: pygame.Surface,
        jugador: pygame.sprite.Sprite,
        grupo_plataformas: pygame.sprite.Group | None,
        grupo_tuberias: pygame.sprite.Group | None,
        grupo_extensores: pygame.sprite.Group | None,
        desplazamiento_camara: pygame.math.Vector2,
        recta_pantalla: pygame.Rect,
    ) -> None:
        if self.limites is None:
            return

        escala = self._escala_base * self.zoom
        if escala <= 0:
            return

        limites = self.limites
        ancho_mundo = limites.width * escala
        alto_mundo = limites.height * escala

        jugador_recta = getattr(jugador, "rect", None)
        if jugador_recta is not None:
            jugador_centro = pygame.Vector2(jugador_recta.centerx, jugador_recta.centery)
        else:
            jugador_centro = pygame.Vector2(limites.centerx, limites.centery)

        def _calcular_offset(tamano_mapa: float, tamano_superficie: float, inicio_limite: float, fin_limite: float, centro_objetivo: float) -> float:
            if tamano_mapa <= tamano_superficie:
                return (tamano_superficie - tamano_mapa) / 2.0
            proporcion = (centro_objetivo - inicio_limite) / max(1.0, fin_limite - inicio_limite)
            posicion_relativa = proporcion * tamano_mapa
            offset = -posicion_relativa + tamano_superficie / 2.0
            max_offset = 0.0
            min_offset = tamano_superficie - tamano_mapa
            return max(min_offset, min(max_offset, offset))

        offset_x = _calcular_offset(
            ancho_mundo,
            self.tamano[0],
            limites.left,
            limites.right,
            jugador_centro.x,
        )
        offset_y = _calcular_offset(
            alto_mundo,
            self.tamano[1],
            limites.top,
            limites.bottom,
            jugador_centro.y,
        )

        self.superficie.fill((0, 0, 0, 0))
        self.superficie.fill(_COLOR_FONDO)

        def convertir_recta(recta_mundo: pygame.Rect) -> pygame.Rect:
            posicion_x = int(offset_x + (recta_mundo.x - limites.left) * escala)
            posicion_y = int(offset_y + (recta_mundo.y - limites.top) * escala)
            ancho = max(1, int(recta_mundo.width * escala))
            alto = max(1, int(recta_mundo.height * escala))
            return pygame.Rect(posicion_x, posicion_y, ancho, alto)

        def blitear_sprite(sprite: pygame.sprite.Sprite) -> pygame.Rect | None:
            if not hasattr(sprite, "rect") or not hasattr(sprite, "image"):
                return None
            recta_sprite_raw = getattr(sprite, "rect")
            if recta_sprite_raw is None:
                return None
            recta_sprite = pygame.Rect(recta_sprite_raw)
            imagen: pygame.Surface | None = getattr(sprite, "image", None)
            if imagen is None:
                return None
            recta_minimapa = convertir_recta(recta_sprite)
            if recta_minimapa.width <= 0 or recta_minimapa.height <= 0:
                return None
            textura = pygame.transform.smoothscale(imagen, (recta_minimapa.width, recta_minimapa.height))
            self.superficie.blit(textura, recta_minimapa.topleft)
            return recta_minimapa

        for plataforma in _iterar_grupo(grupo_plataformas):
            blitear_sprite(plataforma)
        for tuberia in _iterar_grupo(grupo_tuberias):
            recta_tuberia = blitear_sprite(tuberia)
            if recta_tuberia and getattr(tuberia, "danada", False):
                pygame.draw.rect(self.superficie, (255, 120, 80), recta_tuberia, 2)
        for extensor in _iterar_grupo(grupo_extensores):
            blitear_sprite(extensor)

        recta_jugador_origen = getattr(jugador, "rect", None)
        if recta_jugador_origen is not None:
            blitear_sprite(jugador)

        recta_camara_mundo = pygame.Rect(
            int(desplazamiento_camara.x),
            int(desplazamiento_camara.y),
            recta_pantalla.width,
            recta_pantalla.height,
        )
        recta_camara = convertir_recta(recta_camara_mundo)
        pygame.draw.rect(self.superficie, _COLOR_BORDE, recta_camara, 1)

        posicion = (
            recta_pantalla.width - self.tamano[0] - self.margen,
            self.margen,
        )
        superficie_destino.blit(self.superficie, posicion)
        pygame.draw.rect(
            superficie_destino,
            _COLOR_BORDE,
            pygame.Rect(posicion, self.tamano),
            2,
        )
