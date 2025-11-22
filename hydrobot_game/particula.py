import pygame
import random
from rutas import ruta_recurso

RUTAS_PARTICULAS = [
    ruta_recurso("texturas", "obj_ecn", "particulas", "p_agua1.png"),
    ruta_recurso("texturas", "obj_ecn", "particulas", "p_agua2.png"),
    ruta_recurso("texturas", "obj_ecn", "particulas", "p_agua3.png"),
    ruta_recurso("texturas", "obj_ecn", "particulas", "p_agua4.png"),
]


class Particula(pygame.sprite.Sprite):
    def __init__(self, posicion: tuple[int, int], *grupos: pygame.sprite.AbstractGroup) -> None:
        super().__init__(*grupos)
        ruta_elegida = random.choice(RUTAS_PARTICULAS)
        self.image = pygame.image.load(ruta_elegida).convert_alpha()
        self.rect: pygame.Rect = self.image.get_rect(center=posicion)
        self.mascara = pygame.mask.from_surface(self.image)
        self.posicion = pygame.math.Vector2(self.rect.topleft)
        self.velocidad = pygame.math.Vector2(
            random.uniform(-30, 30),
            random.uniform(50, 150)
        )
        self.tiempo_vida = random.uniform(0.5, 1.5)
        self.gravedad = 500.0

    def update(self, dt: float) -> None:
        self.tiempo_vida -= dt
        if self.tiempo_vida <= 0:
            self.kill()
            return
        
        self.velocidad.y += self.gravedad * dt
        self.posicion += self.velocidad * dt
        self.rect.topleft = (round(self.posicion.x), round(self.posicion.y))
