import pygame
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    pass


class SpriteConMascara(pygame.sprite.Sprite):
    """Clase base para sprites que usan máscaras de colisión."""
    
    def obtener_recta_mascara(self) -> pygame.Rect:
        mascara: pygame.mask.Mask = self.mascara  # type: ignore[attr-defined]
        rect: pygame.Rect = self.rect  # type: ignore[assignment]
        rectangulos: list[pygame.Rect] = cast(list[pygame.Rect], list(mascara.get_bounding_rects()))
        if rectangulos:
            recta_relativa = rectangulos[0].copy()
            for recta in rectangulos[1:]:
                recta_relativa.union_ip(recta)
        else:
            recta_relativa = pygame.Rect(0, 0, rect.width, rect.height)
        return recta_relativa.move(rect.topleft)

    def obtener_mascara(self) -> pygame.mask.Mask:
        return self.mascara # type: ignore[attr-defined]
