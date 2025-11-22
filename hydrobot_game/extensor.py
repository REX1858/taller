# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false
import pygame
from typing import Optional, TYPE_CHECKING
from animador import AnimadorGif
from sprite_base import SpriteConMascara
from rutas import ruta_recurso

if TYPE_CHECKING:
    from gestor_sonido import GestorSonido

TAMANO_EXTENSOR = 120
RUTA_EXTENSOR = ruta_recurso("texturas", "robot", "extensor.gif")
RUTA_SONIDO_EXTENSOR = ruta_recurso("sonido", "efectos", "robot", "granbot_movimiento.wav")


class Extensor(SpriteConMascara):
    """Plataforma extensor que el robot puede equipar."""

    _contador_sonido = 0

    def __init__(
        self,
        posicion: tuple[int, int],
        *grupos: pygame.sprite.AbstractGroup,
        gestor_sonido: Optional["GestorSonido"] = None,
    ) -> None:
        super().__init__(*grupos)
        self.animador = AnimadorGif(RUTA_EXTENSOR, velocidad_fotogramas=100)
        self.image: pygame.Surface = self._escalar_fotograma(self.animador.obtener_fotograma_actual())
        self.rect: pygame.Rect = self.image.get_rect(topleft=posicion)
        self.posicion = pygame.math.Vector2(float(posicion[0]), float(posicion[1]))
        self.direccion = 1
        self.mascara = pygame.mask.from_surface(self.image)
        self.velocidad_movimiento = 180.0
        self.moviendo = False
        self.objetivo_jugador: pygame.sprite.Sprite | None = None
        self.velocidad = pygame.math.Vector2(0.0, 0.0)
        self.gravedad = 1200.0
        self.velocidad_caida_maxima = 2400.0
        self.en_suelo = False
        self.atravesando_plataformas = False
        self.tiempo_atravesar_restante = 0.0
        self.gestor_sonido = gestor_sonido
        self.clave_sonido_movimiento = f"movimiento_extensor_{Extensor._contador_sonido}"
        Extensor._contador_sonido += 1
        self.sonido_movimiento_activo = False
        if self.gestor_sonido:
            self.gestor_sonido.registrar_efecto(self.clave_sonido_movimiento, RUTA_SONIDO_EXTENSOR, volumen=0.2)

    def update(self, dt: float = 0.0, grupo_plataformas: pygame.sprite.Group | None = None, recta_limite: pygame.Rect | None = None) -> None:
        self.velocidad.x = 0.0
        if self.moviendo and self.objetivo_jugador is not None and hasattr(self.objetivo_jugador, 'rect'):
            rect_obj = getattr(self.objetivo_jugador, 'rect', None)
            if rect_obj is not None:
                dx = rect_obj.centerx - self.rect.centerx
                if abs(dx) > 3:
                    self.direccion = -1 if dx < 0 else 1
                    self.velocidad.x = self.velocidad_movimiento * ( -1 if dx < 0 else 1 )
                else:
                    # Alineado en X con el jugador: verificar si debe caer
                    self.moviendo = False
                    self.velocidad.x = 0.0
                    if self.rect.bottom < rect_obj.top - 10:
                        self.iniciar_caida_vertical()
                    self.objetivo_jugador = None

        # Temporizador de atravesar plataformas
        if self.atravesando_plataformas:
            self.tiempo_atravesar_restante -= dt
            if self.tiempo_atravesar_restante <= 0.0:
                self.atravesando_plataformas = False

        self.velocidad.y += self.gravedad * dt
        if self.velocidad.y > self.velocidad_caida_maxima:
            self.velocidad.y = self.velocidad_caida_maxima

        posicion_previa = self.posicion.copy()
        self.posicion.x += self.velocidad.x * dt
        self.posicion.y += self.velocidad.y * dt
        self.rect.x = round(self.posicion.x)
        self.rect.y = round(self.posicion.y)

        if grupo_plataformas and self.velocidad.y >= 0 and not self.atravesando_plataformas:
            self._resolver_colision_plataformas(grupo_plataformas, posicion_previa)

        if recta_limite is not None:
            self._aplicar_limites(recta_limite)

        if abs(self.velocidad.x) > 1e-2:
            self.animador.reanudar()
        else:
            self.animador.pausar()
        self.animador.actualizar(dt)
        self._actualizar_imagen()
        self._actualizar_sonido_movimiento()

    def _resolver_colision_plataformas(self, grupo_plataformas: pygame.sprite.Group, posicion_previa: pygame.math.Vector2) -> None:
        hitbox = self.obtener_recta_mascara()
        for plataforma in grupo_plataformas:
            if not hasattr(plataforma, 'obtener_recta_mascara') or not hasattr(plataforma, 'obtener_mascara'):
                continue
            hitbox_plataforma = plataforma.obtener_recta_mascara()
            if not hitbox.colliderect(hitbox_plataforma):
                continue
            mascara_plat = plataforma.obtener_mascara()
            desplazamiento = (plataforma.rect.left - self.rect.left, plataforma.rect.top - self.rect.top)
            if not self.mascara.overlap(mascara_plat, desplazamiento):
                continue
            hitbox_previa = pygame.Rect(
                round(posicion_previa.x) + (hitbox.left - self.rect.left),
                round(posicion_previa.y) + (hitbox.top - self.rect.top),
                hitbox.width,
                hitbox.height
            )
            if hitbox_previa.bottom <= hitbox_plataforma.top:
                diferencia = hitbox.bottom - hitbox_plataforma.top
                self.rect.bottom -= diferencia
                self.posicion.y = float(self.rect.y)
                self.velocidad.y = 0.0
                self.en_suelo = True
                break

    def _aplicar_limites(self, recta_limite: pygame.Rect) -> None:
        hitbox = self.obtener_recta_mascara()
        if hitbox.left < recta_limite.left:
            delta = recta_limite.left - hitbox.left
            self.rect.left += delta
            self.posicion.x = float(self.rect.x)
        if hitbox.right > recta_limite.right:
            delta = hitbox.right - recta_limite.right
            self.rect.right -= delta
            self.posicion.x = float(self.rect.x)
        hitbox = self.obtener_recta_mascara()
        if hitbox.bottom > recta_limite.bottom:
            delta = hitbox.bottom - recta_limite.bottom
            self.rect.bottom -= delta
            self.posicion.y = float(self.rect.y)
            self.velocidad.y = 0.0
            self.en_suelo = True

    def establecer_direccion(self, direccion: int) -> None:
        nueva_direccion = -1 if direccion < 0 else 1
        if nueva_direccion == self.direccion:
            return
        posicion_actual = self.rect.midbottom
        self.direccion = nueva_direccion
        self._actualizar_imagen()
        self.rect = self.image.get_rect(midbottom=posicion_actual)
        self.posicion.update(self.rect.topleft)
        self.mascara = pygame.mask.from_surface(self.image)

    def ordenar_ir_a_jugador(self, jugador: pygame.sprite.Sprite) -> None:
        # Si ya está alineado en X con el jugador, verificar si debe caer
        if hasattr(jugador, 'rect'):
            rect_j = getattr(jugador, 'rect')
            tolerancia_x = 8
            if abs(self.rect.centerx - rect_j.centerx) <= tolerancia_x:
                if self.rect.bottom < rect_j.top - 10:
                    self.iniciar_caida_vertical()
                return
        self.objetivo_jugador = jugador
        self.moviendo = True

    def iniciar_caida_vertical(self) -> None:
        """Activa el modo de atravesar plataformas temporalmente para dejarse caer."""
        self.atravesando_plataformas = True
        self.tiempo_atravesar_restante = 0.25
        # Asegurar velocidad hacia abajo para despegarse de la superficie
        if self.velocidad.y < 120.0:
            self.velocidad.y = 120.0
        self.en_suelo = False

    def _escalar_fotograma(self, fotograma: pygame.Surface) -> pygame.Surface:
        return pygame.transform.scale(fotograma, (TAMANO_EXTENSOR, TAMANO_EXTENSOR))

    def _actualizar_imagen(self) -> None:
        fotograma = self.animador.obtener_fotograma_actual()
        imagen: pygame.Surface = self._escalar_fotograma(fotograma)
        if self.direccion < 0:
            imagen = pygame.transform.flip(imagen, True, False)
        self.image = imagen
        self.mascara = pygame.mask.from_surface(self.image)

    def _actualizar_sonido_movimiento(self) -> None:
        if not self.gestor_sonido:
            return
        en_movimiento = self.moviendo and abs(self.velocidad.x) > 1e-2
        if en_movimiento:
            if not self.sonido_movimiento_activo:
                canal = self.gestor_sonido.reproducir_efecto(self.clave_sonido_movimiento, loops=-1, reiniciar=True)
                if canal:
                    self.sonido_movimiento_activo = True
        else:
            self._detener_sonido_movimiento()

    def _detener_sonido_movimiento(self) -> None:
        if not self.gestor_sonido or not self.sonido_movimiento_activo:
            self.sonido_movimiento_activo = False
            return
        self.gestor_sonido.detener_efecto(self.clave_sonido_movimiento)
        self.sonido_movimiento_activo = False

    def kill(self) -> None:
        self._detener_sonido_movimiento()
        super().kill()
