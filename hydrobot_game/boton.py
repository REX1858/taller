import pygame


class Boton:
    def __init__(self, texto: str, centro: tuple[int, int], tamano: tuple[int, int], textura: pygame.Surface | str | None = None) -> None:
        self.texto = texto
        self.recta = pygame.Rect(0, 0, tamano[0], tamano[1])
        self.recta.center = centro
        self.color_base = (72, 82, 110)
        self.color_resaltado = (110, 130, 170)
        self.textura: pygame.Surface | None = None
        if isinstance(textura, pygame.Surface):
            self.textura = pygame.transform.smoothscale(textura, self.recta.size)
        elif isinstance(textura, str):
            try:
                imagen = pygame.image.load(textura).convert_alpha()
                self.textura = pygame.transform.smoothscale(imagen, self.recta.size)
            except pygame.error:
                self.textura = None
        else:
            self.textura = None

    def dibujar(self, superficie: pygame.Surface, fuente: pygame.font.Font) -> None:
        posicion_raton = pygame.mouse.get_pos()
        resaltado = self.recta.collidepoint(posicion_raton)
        if self.textura:
            superficie.blit(self.textura, self.recta.topleft)
            if resaltado:
                capa_resaltado = pygame.Surface(self.recta.size, pygame.SRCALPHA)
                capa_resaltado.fill((40, 45, 60, 90))
                superficie.blit(capa_resaltado, self.recta.topleft)
        else:
            color_actual = self.color_resaltado if resaltado else self.color_base
            pygame.draw.rect(superficie, color_actual, self.recta, border_radius=10)
            pygame.draw.rect(superficie, (18, 20, 28), self.recta, 2, border_radius=10)
        texto_render = fuente.render(self.texto, True, (230, 230, 235))
        recta_texto = texto_render.get_rect(center=self.recta.center)
        superficie.blit(texto_render, recta_texto)

    def fue_clic(self, evento: pygame.event.Event) -> bool:
        return (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and self.recta.collidepoint(evento.pos)
        )
