import pygame
import random
from typing import TYPE_CHECKING, Optional, cast
from sprite_base import SpriteConMascara
from rutas import ruta_recurso

if TYPE_CHECKING:
    from gestor_sonido import GestorSonido

RUTA_TUBERIA = ruta_recurso("texturas", "obj_ecn", "tuberia_h.png")
RUTA_ROTO1 = ruta_recurso("texturas", "obj_ecn", "particulas", "roto1.png")
RUTA_ROTO2 = ruta_recurso("texturas", "obj_ecn", "particulas", "roto2.png")
RUTA_ROTO3 = ruta_recurso("texturas", "obj_ecn", "particulas", "roto3.png")
RUTA_SONIDO_AGUA = ruta_recurso("sonido", "efectos", "agua1.wav")
RUTA_PARCHE1 = ruta_recurso("sonido", "efectos", "parche1.ogg")
RUTA_PARCHE2 = ruta_recurso("sonido", "efectos", "parche2.ogg")


class Tuberia(SpriteConMascara):
    _tuberia_sonando: "Tuberia | None" = None
    _sonido_registrado = False
    CLAVE_SONIDO_AGUA = "sonido_agua_fuga"
    REDUCCION_SUPERIOR = 16

    def __init__(
        self,
        posicion: tuple[int, int],
        danada: bool = False,
        gestor_sonido: Optional["GestorSonido"] = None,
        *grupos: pygame.sprite.AbstractGroup,
        ruta_imagen: str | None = None,
    ) -> None:
        super().__init__(*grupos)
        ruta = ruta_imagen or RUTA_TUBERIA
        self.imagen_original = pygame.image.load(ruta).convert_alpha()
        ancho_escalado = int(self.imagen_original.get_width() * 7)
        alto_escalado = int(self.imagen_original.get_height() * 7)
        self.image = pygame.transform.scale(self.imagen_original, (ancho_escalado, alto_escalado))
        self.rect: pygame.Rect = self.image.get_rect(topleft=posicion)
        self.mascara = pygame.mask.from_surface(self.image)
        self._reducir_mascara_superior(self.REDUCCION_SUPERIOR)
        self.posicion = pygame.math.Vector2(posicion)
        self.orientacion = "horizontal"
        self.requiere_caida = False
        self.en_caida = False
        self.destino_caida_y: float | None = None
        self.velocidad_caida = 320.0
        self.caida_completada = False
        self.danada = danada
        self.reparada = False
        self.tiempo_particula = 0.0
        self.intervalo_particula = 0.2
        self.decal_superficie: pygame.Surface | None = None
        self.decal_rect: pygame.Rect | None = None
        self.nivel_rotura = 1
        self.factor_particulas = 1
        self.tiempo_danada = 0.0
        self.tiempo_para_escalar = 30.0
        self.gestor_sonido = gestor_sonido
        self.sonido_agua_en_bucle = False
        self.clave_sonido_agua = self.CLAVE_SONIDO_AGUA
        if self.gestor_sonido and not Tuberia._sonido_registrado:
            self.gestor_sonido.registrar_efecto(self.clave_sonido_agua, RUTA_SONIDO_AGUA, volumen=0.25)
            Tuberia._sonido_registrado = True
        if self.danada:
            self._preparar_decal()

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

    def update(self, dt: float, grupo_particulas: pygame.sprite.Group | None = None) -> None:
        if self.en_caida:
            self._detener_sonido_agua()
            if self.destino_caida_y is None:
                self.en_caida = False
                return
            if self.posicion.y < self.destino_caida_y:
                self.posicion.y = min(self.destino_caida_y, self.posicion.y + self.velocidad_caida * dt)
                self.rect.y = int(self.posicion.y)
            else:
                self.posicion.y = float(self.destino_caida_y)
                self.rect.y = int(self.destino_caida_y)
                self.en_caida = False
                self.caida_completada = True
            return

        if not self.danada or self.reparada:
            self._detener_sonido_agua()
            return

        self._asegurar_sonido_agua()

        self.tiempo_danada += dt
        if self.tiempo_danada >= self.tiempo_para_escalar:
            self.tiempo_danada = 0.0
            self._escalar_rotura()

        if grupo_particulas is None:
            return
        
        self.tiempo_particula += dt
        if self.tiempo_particula >= self.intervalo_particula:
            self.tiempo_particula = 0.0
            from particula import Particula
            cantidad = self.factor_particulas
            for _ in range(cantidad):
                posicion_particula = (
                    self.rect.centerx + random.randint(-12, 12),
                    self.rect.centery + random.randint(-12, 12)
                )
                Particula(posicion_particula, grupo_particulas)

    def obtener_recta_reparacion(self) -> pygame.Rect:
        if not self.danada or self.decal_rect is None:
            return self.obtener_recta_mascara()
        return self.decal_rect.copy()

    def reparar(self) -> None:
        self.reparada = True
        self.danada = False
        
        if self.decal_superficie and self.decal_rect:
            self._convertir_decal_a_gris()
        
        self.tiempo_particula = 0.0
        self.nivel_rotura = 0
        self.factor_particulas = 0
        self.tiempo_danada = 0.0
        self._detener_sonido_agua()
        if self.gestor_sonido:
            self.gestor_sonido.reproducir_efecto_puntual(random.choice([RUTA_PARCHE1, RUTA_PARCHE2]), volumen=0.5)

    def iniciar_caida(self, altura_mundo: int) -> None:
        destino = max(0, altura_mundo - self.rect.height)
        self.destino_caida_y = float(destino)
        if self.posicion.y >= self.destino_caida_y:
            self.posicion.y = float(destino)
            self.rect.y = destino
            self.en_caida = False
            self.caida_completada = True
            self.requiere_caida = False
            return
        self.en_caida = True
        self.requiere_caida = False
        self.caida_completada = False

    def _preparar_decal(self, nivel: int | None = None) -> None:
        rutas = [RUTA_ROTO1, RUTA_ROTO2, RUTA_ROTO3]
        try:
            if nivel is None:
                ruta = random.choice(rutas)
            else:
                if nivel <= 1:
                    ruta = RUTA_ROTO1
                elif nivel == 2:
                    ruta = RUTA_ROTO2
                else:
                    ruta = RUTA_ROTO3
            imagen = pygame.image.load(ruta).convert_alpha()
            rotacion = random.choice([0, 90, 180, 270])
            imagen = pygame.transform.rotate(imagen, rotacion)
            escala = 4
            imagen = pygame.transform.scale(imagen, (imagen.get_width() * escala, imagen.get_height() * escala))
            self.decal_superficie = imagen
            self.decal_rect = imagen.get_rect(center=self.rect.center)
            if "roto1" in ruta:
                self.nivel_rotura = 1
            elif "roto2" in ruta:
                self.nivel_rotura = 2
            elif "roto3" in ruta:
                self.nivel_rotura = 3
            else:
                self.nivel_rotura = 1
            self._calcular_factor_particulas()
        except pygame.error:
            self.decal_superficie = None
            self.decal_rect = None
            self.nivel_rotura = 1
            self._calcular_factor_particulas()

    def obtener_decal(self) -> tuple[pygame.Surface, pygame.Rect] | None:
        if not self.danada and not self.reparada:
            return None
        if self.decal_superficie is None or self.decal_rect is None:
            self._preparar_decal()
        if self.decal_superficie is None or self.decal_rect is None:
            return None
        self.decal_rect.center = self.rect.center
        return self.decal_superficie, self.decal_rect

    def _calcular_factor_particulas(self) -> None:
        # Ajustar densidad de fuga segun nivel (mas nivel -> mas particulas y menor intervalo)
        if self.nivel_rotura <= 1:
            self.factor_particulas = 1
            self.intervalo_particula = 0.04  
        elif self.nivel_rotura == 2:
            self.factor_particulas = 2
            self.intervalo_particula = 0.02
        else:
            self.factor_particulas = 3
            self.intervalo_particula = 0.01

    def _escalar_rotura(self) -> None:
        if not self.danada:
            return
        if self.nivel_rotura < 3:
            self.nivel_rotura += 1
            self._preparar_decal(self.nivel_rotura)
        self._calcular_factor_particulas()

    def _asegurar_sonido_agua(self) -> None:
        if not self.gestor_sonido:
            return
        tuberia_activa = Tuberia._tuberia_sonando
        if tuberia_activa and not tuberia_activa.alive():
            tuberia_activa = None
            Tuberia._tuberia_sonando = None
        if tuberia_activa and tuberia_activa is not self:
            if not tuberia_activa.danada or tuberia_activa.reparada:
                tuberia_activa._detener_sonido_agua()
                tuberia_activa = None
            else:
                self.sonido_agua_en_bucle = False
                return
        if Tuberia._tuberia_sonando is None:
            Tuberia._tuberia_sonando = self
        if Tuberia._tuberia_sonando is not self:
            self.sonido_agua_en_bucle = False
            return
        if not self.sonido_agua_en_bucle:
            canal = self.gestor_sonido.reproducir_efecto(self.clave_sonido_agua, loops=-1, reiniciar=True)
            if canal:
                self.sonido_agua_en_bucle = True
        elif not self.gestor_sonido.esta_reproduciendo(self.clave_sonido_agua):
            canal = self.gestor_sonido.reproducir_efecto(self.clave_sonido_agua, loops=-1, reiniciar=True)
            if canal:
                self.sonido_agua_en_bucle = True

    def _detener_sonido_agua(self) -> None:
        if self.gestor_sonido and self.sonido_agua_en_bucle and Tuberia._tuberia_sonando is self:
            self.gestor_sonido.detener_efecto(self.clave_sonido_agua)
        if Tuberia._tuberia_sonando is self:
            Tuberia._tuberia_sonando = None
        self.sonido_agua_en_bucle = False

    def _convertir_decal_a_gris(self) -> None:
        if not self.decal_superficie:
            return
        superficie_gris = self.decal_superficie.copy()
        ancho, alto = superficie_gris.get_size()
        superficie_gris.lock()
        for x in range(ancho):
            for y in range(alto):
                color = superficie_gris.get_at((x, y))
                if color.a > 0:
                    gris_base = int(color.r * 0.299 + color.g * 0.587 + color.b * 0.114)
                    gris_claro = min(255, int(gris_base * 0.4 + 150))
                    superficie_gris.set_at((x, y), (gris_claro, gris_claro, gris_claro, color.a))
        superficie_gris.unlock()
        self.decal_superficie = superficie_gris
