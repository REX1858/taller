import pygame


class NPCTutorial:
    def __init__(self, ruta_imagen: str, radio_interaccion: int = 120, factor_escala: float = 1.5) -> None:
        self.ruta_imagen = ruta_imagen
        self.radio_interaccion = radio_interaccion
        self.factor_escala = factor_escala
        self.recta: pygame.Rect | None = None
        self.imagen_original: pygame.Surface | None = None
        self.imagen_volteada: pygame.Surface | None = None
        self.imagen_actual: pygame.Surface | None = None
        self.dialogos: list[str] = []
        self.indice_dialogo = 0

    def reiniciar(self) -> None:
        self.recta = None
        self.imagen_original = None
        self.imagen_volteada = None
        self.imagen_actual = None
        self.dialogos = []
        self.indice_dialogo = 0

    def cargar(self, recta_meta: pygame.Rect) -> None:
        try:
            imagen = pygame.image.load(self.ruta_imagen).convert_alpha()
        except pygame.error:
            self.reiniciar()
            return
        if imagen.get_height() > 0:
            alto_objetivo = int(recta_meta.height * self.factor_escala)
            factor = alto_objetivo / imagen.get_height()
            imagen = pygame.transform.smoothscale(
                imagen,
                (
                    max(1, int(imagen.get_width() * factor)),
                    alto_objetivo,
                ),
            )
        self.imagen_original = imagen
        self.imagen_volteada = pygame.transform.flip(imagen, True, False)
        self.imagen_actual = self.imagen_original
        self.recta = imagen.get_rect(midbottom=recta_meta.midbottom)

    def asignar_dialogos(self, dialogos: list[str]) -> None:
        self.dialogos = dialogos
        self.indice_dialogo = 0

    def obtener_dialogo_actual(self) -> str | None:
        if not self.dialogos:
            return None
        return self.dialogos[self.indice_dialogo]

    def avanzar_dialogo(self) -> None:
        if not self.dialogos:
            return
        self.indice_dialogo = (self.indice_dialogo + 1) % len(self.dialogos)

    def esta_disponible(self) -> bool:
        return self.recta is not None and self.imagen_actual is not None

    def en_rango(self, recta_jugador: pygame.Rect) -> bool:
        if not self.esta_disponible():
            return False
        assert self.recta is not None
        area = self.recta.inflate(self.radio_interaccion, self.radio_interaccion)
        return area.colliderect(recta_jugador)

    def actualizar_orientacion(self, recta_jugador: pygame.Rect) -> None:
        if not self.esta_disponible():
            return
        assert self.recta is not None
        assert self.imagen_original is not None
        assert self.imagen_volteada is not None
        if recta_jugador.centerx < self.recta.centerx:
            self.imagen_actual = self.imagen_volteada
        else:
            self.imagen_actual = self.imagen_original

    def dibujar(self, superficie: pygame.Surface, desplazamiento: tuple[int, int]) -> pygame.Rect | None:
        if not self.esta_disponible():
            return None
        assert self.recta is not None
        assert self.imagen_actual is not None
        offset_x, offset_y = desplazamiento
        destino = self.recta.move(-offset_x, -offset_y)
        superficie.blit(self.imagen_actual, destino.topleft)
        return destino
