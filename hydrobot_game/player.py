import pygame
from typing import TYPE_CHECKING
from animador import AnimadorGif
from tuberia import Tuberia
from sprite_base import SpriteConMascara
from rutas import ruta_recurso

if TYPE_CHECKING:
    from gestor_sonido import GestorSonido


class Jugador(SpriteConMascara):
    """Jugador plataformero con sistema de extensor."""

    def __init__(
        self,
        posicion_inicio: tuple[int, int],
        gestor_sonido: "GestorSonido",
        tamano: int = 120,
        *grupos: pygame.sprite.AbstractGroup,
    ) -> None:
        super().__init__(*grupos)
        
        self.gestor_sonido = gestor_sonido
        self.tiene_extensor = True
        self.ruta_robot_andar = ruta_recurso("texturas", "robot", "robot_andar.gif")
        self.ruta_robot_correr = ruta_recurso("texturas", "robot", "robot_correr.gif")
        self.ruta_granbot_andar = ruta_recurso("texturas", "robot", "granbot_andar.gif")
        self.ruta_granbot_correr = ruta_recurso("texturas", "robot", "granbot_correr.gif")
        
        self.tamano_sprite = tamano
        
        self.animador_andar: AnimadorGif | None = None
        self.animador_correr: AnimadorGif | None = None
        self.animador_actual: AnimadorGif | None = None
        
        self._cargar_animadores()
        self._actualizar_stats()
        
        self.image = self._escalar_fotograma(self.animador_actual.obtener_fotograma_actual()) if self.animador_actual else pygame.Surface((tamano, tamano))
        self.rect: pygame.Rect = self.image.get_rect(topleft=posicion_inicio)
        self.mascara = pygame.mask.from_surface(self.image)

        self.posicion = pygame.math.Vector2(posicion_inicio)
        self.velocidad = pygame.math.Vector2(0.0, 0.0)

        self.en_suelo = False
        self.puede_saltar = True
        self.ultima_direccion = 1
        self.corriendo = False
        
        self.sobre_extensor = False
        self.sobre_plataforma = False
        self.sobre_tuberia = False
        self.posicion_extensor_soltado: tuple[int, int] | None = None
        self.extensor_equipado = False
        self.recta_extensor_actual: pygame.Rect | None = None
        self.extensor_objetivo: pygame.sprite.Sprite | None = None
        self.extensor_recien_creado = False
        self.direccion_extensor_soltado = 1
        self.cooldown_e = 0.0
        self.tiempo_cooldown_e = 0.3
        self.ruta_robot_soldar = ruta_recurso("texturas", "robot", "soldar.gif")
        self.animador_soldar: AnimadorGif | None = None
        self.soldando = False
        self.tiempo_soldadura_total = 3.0
        self.tiempo_soldadura_restante = 0.0
        self.tuberia_objetivo_soldar: Tuberia | None = None
        self.tiempo_gracia_borde = 0.1
        self.tiempo_gracia_restante = 0.0
        self.area_busqueda_reparacion: pygame.Rect | None = None
        self.tuberias_en_rango: list[Tuberia] = []
        
        self.ruta_robot_movimiento = ruta_recurso("sonido", "efectos", "robot", "robot_movimiento.wav")
        self.ruta_granbot_movimiento = ruta_recurso("sonido", "efectos", "robot", "granbot_movimiento.wav")
        self.ruta_granbot_bajar = ruta_recurso("sonido", "efectos", "robot", "granbot_bajar.wav")
        self.ruta_soldar1 = ruta_recurso("sonido", "efectos", "soldar1.wav")
        self.ruta_soldar2 = ruta_recurso("sonido", "efectos", "soldar2.wav")
        self.clave_movimiento_robot = "movimiento_robot"
        self.clave_movimiento_granbot = "movimiento_granbot"
        self.clave_movimiento_activa: str | None = None
        self.clave_soldadura_inicio = "soldadura_inicio"
        self.clave_soldadura_bucle = "soldadura_bucle"
        self.clave_extensor_bajar = "extensor_bajar"
        self._registrar_efectos_sonido()

    def _cargar_animadores(self) -> None:
        if self.tiene_extensor:
            self.animador_andar = AnimadorGif(self.ruta_granbot_andar, velocidad_fotogramas=100)
            self.animador_correr = AnimadorGif(self.ruta_granbot_correr, velocidad_fotogramas=80)
            self.animador_soldar = None
        else:
            self.animador_andar = AnimadorGif(self.ruta_robot_andar, velocidad_fotogramas=100)
            self.animador_correr = AnimadorGif(self.ruta_robot_correr, velocidad_fotogramas=80)
            self.animador_soldar = AnimadorGif(self.ruta_robot_soldar, velocidad_fotogramas=100)
        self.animador_actual = self.animador_andar

    def _registrar_efectos_sonido(self) -> None:
        self.gestor_sonido.registrar_efecto(self.clave_movimiento_robot, self.ruta_robot_movimiento, canal=1, volumen=0.35)
        self.gestor_sonido.registrar_efecto(self.clave_movimiento_granbot, self.ruta_granbot_movimiento, canal=1, volumen=0.2)
        self.gestor_sonido.registrar_efecto(self.clave_extensor_bajar, self.ruta_granbot_bajar, volumen=0.2)
        self.gestor_sonido.registrar_efecto(self.clave_soldadura_inicio, self.ruta_soldar1, canal=2, volumen=0.2)
        self.gestor_sonido.registrar_efecto(self.clave_soldadura_bucle, self.ruta_soldar2, canal=3, volumen=0.2)

    def _detener_sonido_movimiento(self) -> None:
        if self.clave_movimiento_activa is None:
            return
        self.gestor_sonido.detener_efecto(self.clave_movimiento_activa)
        self.clave_movimiento_activa = None

    def _actualizar_stats(self) -> None:
        if self.tiene_extensor:
            self.velocidad_movimiento = 400.0
            self.velocidad_salto = 710.0
        else:
            self.velocidad_movimiento = 200.0
            self.velocidad_salto = 530.0
        
        self.gravedad = 1200.0
        self.velocidad_caida_maxima = 2400.0

    def equipar_extensor(self, recta_extensor: pygame.Rect | None = None) -> None:
        self.tiene_extensor = True
        self._detener_sonido_movimiento()
        self._cargar_animadores()
        self._actualizar_stats()
        self._registrar_efectos_sonido()
        self.gestor_sonido.reproducir_efecto(self.clave_extensor_bajar, reiniciar=True)
        if recta_extensor:
            self.rect.midbottom = recta_extensor.midbottom
            self.posicion.update(self.rect.topleft)

    def desequipar_extensor(self) -> tuple[int, int]:
        self.tiene_extensor = False
        self._detener_sonido_movimiento()
        self._cargar_animadores()
        self._actualizar_stats()
        self._registrar_efectos_sonido()
        self.gestor_sonido.reproducir_efecto(self.clave_extensor_bajar, reiniciar=True)
        self.direccion_extensor_soltado = self.ultima_direccion or 1
        posicion_extensor = (int(self.rect.centerx), int(self.rect.bottom))
        return posicion_extensor

    def update(self, teclas: pygame.key.ScancodeWrapper, dt: float, recta_limite: pygame.Rect, grupo_extensores: pygame.sprite.Group | None = None, grupo_plataformas: pygame.sprite.Group | None = None, grupo_tuberias: pygame.sprite.Group | None = None) -> None:
        if self.soldando:
            self.velocidad.x = 0.0
            self.velocidad.y = 0.0
            self._detener_sonido_movimiento()
            self.tiempo_soldadura_restante -= dt
            if self.animador_soldar:
                self.animador_actual = self.animador_soldar
                self.animador_soldar.reanudar()
                self.animador_soldar.actualizar(dt)
            if self.tiempo_soldadura_restante <= 0.0:
                self.soldando = False
                self.gestor_sonido.detener_efecto(self.clave_soldadura_bucle)
                if isinstance(self.tuberia_objetivo_soldar, Tuberia):
                    try:
                        self.tuberia_objetivo_soldar.reparar()
                    except Exception:
                        pass
                self.tuberia_objetivo_soldar = None
                self.animador_actual = self.animador_andar
            else:
                self._actualizar_imagen()
                return
        self.sobre_extensor = False
        self.sobre_plataforma = False
        self.sobre_tuberia = False
        self.recta_extensor_actual = None
        self.extensor_objetivo = None
        if grupo_extensores:
            self._detectar_extensor(grupo_extensores)
        
        if grupo_tuberias and not self.tiene_extensor and self.en_suelo:
            self._detectar_tuberia_debajo(grupo_tuberias)
        
        self.posicion_extensor_soltado = None
        self.extensor_equipado = False
        
        if self.cooldown_e > 0.0:
            self.cooldown_e -= dt
        
        hitbox_inicial = self.obtener_recta_mascara()
        self.en_suelo = hitbox_inicial.bottom >= recta_limite.bottom
        
        self._mover_horizontal(teclas)
        self._manejar_salto(teclas)
        self._aplicar_gravedad(dt)
        
        posicion_previa = self.posicion.copy()
        self._aplicar_velocidad(dt)
        
        if grupo_plataformas and self.velocidad.y >= 0:
            self._manejar_colision_plataforma(grupo_plataformas, posicion_previa)
        if grupo_extensores and self.velocidad.y >= 0:
            self._manejar_colision_plataforma(grupo_extensores, posicion_previa)
        if grupo_tuberias and not self.tiene_extensor and self.velocidad.y >= 0:
            self._manejar_colision_plataforma(grupo_tuberias, posicion_previa)
        
        hitbox_post = self.obtener_recta_mascara()
        if hitbox_post.bottom < recta_limite.bottom and not (self.sobre_extensor or self.sobre_plataforma or self.sobre_tuberia):
            self.en_suelo = False
        else:
            self.en_suelo = True
        if not self.en_suelo:
            self.puede_saltar = False

        # Ayuda anti-desnivel para tuberias h±1: evitar caidas por pequeños escalones
        self.tiempo_gracia_restante = max(0.0, self.tiempo_gracia_restante - dt)
        tecla_bajar = teclas[pygame.K_s] or teclas[pygame.K_DOWN]
        if (not self.en_suelo) and self.tiempo_gracia_restante > 0.0 and self.velocidad.y >= 0.0 and not tecla_bajar:
            self._intentar_snap_suelo(hitbox_post, (grupo_plataformas, grupo_extensores, grupo_tuberias))
        
        self._manejar_bajar_plataforma(teclas, grupo_plataformas)
        self._manejar_tecla_f(teclas, grupo_tuberias)
        self.posicion_extensor_soltado = self._manejar_tecla_e(teclas)
        
        self._limitar_a_espacio(recta_limite)
        self._actualizar_animacion(dt)
        self._manejar_sonido_movimiento()
        self._actualizar_imagen()
        
        if (
            self.extensor_equipado
            and grupo_extensores
            and self.extensor_objetivo is not None
            and self.extensor_objetivo in grupo_extensores
        ):
            extensor_actual = self.extensor_objetivo
            if hasattr(extensor_actual, "_detener_sonido_movimiento"):
                try:
                    extensor_actual._detener_sonido_movimiento()  # type: ignore[attr-defined]
                except Exception:
                    pass
            grupo_extensores.remove(extensor_actual)
        self.recta_extensor_actual = None
        self.extensor_objetivo = None

    def _mover_horizontal(self, teclas: pygame.key.ScancodeWrapper) -> None:
        self.velocidad.x = 0.0
        self.corriendo = False
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            self.velocidad.x = -self.velocidad_movimiento
            self.ultima_direccion = -1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            self.velocidad.x = self.velocidad_movimiento
            self.ultima_direccion = 1

        if (
            teclas[pygame.K_LSHIFT]
            or teclas[pygame.K_RSHIFT]
            or teclas[pygame.K_LEFTBRACKET]
            or teclas[pygame.K_RIGHTBRACKET]
        ):
            if self.velocidad.x != 0.0:
                self.corriendo = True
                self.velocidad.x *= 1.5

    def _manejar_sonido_movimiento(self) -> None:
        clave_objetivo = self.clave_movimiento_granbot if self.tiene_extensor else self.clave_movimiento_robot

        if self.soldando:
            self._detener_sonido_movimiento()
            return

        en_movimiento = abs(self.velocidad.x) > 1e-2

        if en_movimiento:
            if self.clave_movimiento_activa and self.clave_movimiento_activa != clave_objetivo:
                self._detener_sonido_movimiento()
            self.clave_movimiento_activa = clave_objetivo
            self.gestor_sonido.reproducir_efecto(clave_objetivo, loops=-1, reiniciar=False)
        else:
            self._detener_sonido_movimiento()

    def _manejar_salto(self, teclas: pygame.key.ScancodeWrapper) -> None:
        desea_saltar = teclas[pygame.K_w] or teclas[pygame.K_SPACE] or teclas[pygame.K_UP]
        if desea_saltar and self.puede_saltar:
            self.velocidad.y = -self.velocidad_salto
            self.puede_saltar = False
    
    def _manejar_bajar_plataforma(self, teclas: pygame.key.ScancodeWrapper, grupo_plataformas: pygame.sprite.Group | None) -> None:
        if not (teclas[pygame.K_s] or teclas[pygame.K_DOWN]):
            return
        
        if not (self.sobre_plataforma or self.sobre_extensor or self.sobre_tuberia):
            return
        
        self.posicion.y += 10
        self.rect.topleft = (round(self.posicion.x), round(self.posicion.y))
        self.sobre_plataforma = False
        self.sobre_extensor = False
        self.sobre_tuberia = False
        self.en_suelo = False
        self.puede_saltar = False

    def _aplicar_gravedad(self, dt: float) -> None:
        self.velocidad.y += self.gravedad * dt
        if self.velocidad.y > self.velocidad_caida_maxima:
            self.velocidad.y = self.velocidad_caida_maxima

    def _aplicar_velocidad(self, dt: float) -> None:
        self.posicion.x += self.velocidad.x * dt
        self.posicion.y += self.velocidad.y * dt
        self.rect.topleft = (round(self.posicion.x), round(self.posicion.y))

    def _limitar_a_espacio(self, recta_limite: pygame.Rect) -> None:
        hitbox = self.obtener_recta_mascara()
        
        if hitbox.left < recta_limite.left:
            desplazamiento = recta_limite.left - hitbox.left
            self.rect.left += desplazamiento
            self.posicion.x = float(self.rect.x)
        if hitbox.right > recta_limite.right:
            desplazamiento = hitbox.right - recta_limite.right
            self.rect.right -= desplazamiento
            self.posicion.x = float(self.rect.x)

        hitbox = self.obtener_recta_mascara()
        if hitbox.bottom >= recta_limite.bottom:
            desplazamiento = hitbox.bottom - recta_limite.bottom
            self.rect.bottom -= desplazamiento
            self.posicion.y = float(self.rect.y)
            self.velocidad.y = 0.0
            self.en_suelo = True
            self.puede_saltar = True

        if hitbox.top < recta_limite.top:
            desplazamiento = recta_limite.top - hitbox.top
            self.rect.top += desplazamiento
            self.posicion.y = float(self.rect.y)
            self.velocidad.y = 0.0

    def _actualizar_animacion(self, dt: float) -> None:
        if self.animador_actual is None:
            return
        if self.soldando:
            return
            
        animador_nuevo = self.animador_correr if self.corriendo else self.animador_andar
        
        if animador_nuevo != self.animador_actual:
            self.animador_actual = animador_nuevo
            if self.animador_actual:
                self.animador_actual.reiniciar()
        
        if self.animador_actual:
            if self.velocidad.x == 0.0:
                self.animador_actual.pausar()
            else:
                self.animador_actual.reanudar()
            self.animador_actual.actualizar(dt)

    def _actualizar_imagen(self) -> None:
        if self.animador_actual is None:
            return
            
        fotograma = self.animador_actual.obtener_fotograma_actual()
        imagen_escalada = self._escalar_fotograma(fotograma)
        
        if self.ultima_direccion < 0:
            imagen_escalada = pygame.transform.flip(imagen_escalada, True, False)
        
        self.image = imagen_escalada
        self.mascara = pygame.mask.from_surface(self.image)

    def _detectar_extensor(self, grupo_extensores: pygame.sprite.Group) -> None:
        if self.mascara.count() == 0:
            return
        for extensor in grupo_extensores:
            if not hasattr(extensor, "obtener_mascara"):
                continue
            mascara_sprite = extensor.obtener_mascara()
            if mascara_sprite.count() == 0:
                continue
            desplazamiento = (extensor.rect.left - self.rect.left, extensor.rect.top - self.rect.top)
            if self.mascara.overlap(mascara_sprite, desplazamiento):
                self.sobre_extensor = True
                self.recta_extensor_actual = extensor.obtener_recta_mascara().copy()
                self.extensor_objetivo = extensor
                break

    def _detectar_tuberia_debajo(self, grupo_tuberias: pygame.sprite.Group) -> None:
        if self.mascara.count() == 0:
            return
        hitbox_jugador = self.obtener_recta_mascara()
        margen_deteccion = 5
        for tuberia in grupo_tuberias:
            if not hasattr(tuberia, "obtener_recta_mascara"):
                continue
            hitbox_tuberia = tuberia.obtener_recta_mascara()
            if abs(hitbox_jugador.bottom - hitbox_tuberia.top) <= margen_deteccion:
                if not (hitbox_jugador.right <= hitbox_tuberia.left or hitbox_jugador.left >= hitbox_tuberia.right):
                    self.sobre_tuberia = True
                    break

    def _manejar_colision_plataforma(self, grupo_extensores: pygame.sprite.Group, posicion_previa: pygame.math.Vector2) -> None:
        hitbox = self.obtener_recta_mascara()
        for extensor in grupo_extensores:
            hitbox_extensor = extensor.obtener_recta_mascara()
            if not hitbox.colliderect(hitbox_extensor):
                continue
            
            mascara_extensor = extensor.obtener_mascara()
            desplazamiento = (extensor.rect.left - self.rect.left, extensor.rect.top - self.rect.top)
            if not self.mascara.overlap(mascara_extensor, desplazamiento):
                continue
            
            hitbox_previa = pygame.Rect(
                round(posicion_previa.x) + (hitbox.left - self.rect.left),
                round(posicion_previa.y) + (hitbox.top - self.rect.top),
                hitbox.width,
                hitbox.height
            )
            
            if hitbox_previa.bottom <= hitbox_extensor.top:
                diferencia = hitbox.bottom - hitbox_extensor.top
                self.rect.bottom -= diferencia
                self.posicion.y = float(self.rect.y)
                self.velocidad.y = 0.0
                self.en_suelo = True
                self.puede_saltar = True
                self.tiempo_gracia_restante = self.tiempo_gracia_borde
                
                from plataforma import Plataforma
                from tuberia import Tuberia
                if isinstance(extensor, Plataforma):
                    self.sobre_plataforma = True
                elif isinstance(extensor, Tuberia) and not self.tiene_extensor:
                    self.sobre_tuberia = True
                else:
                    self.sobre_extensor = True
                break

    def _intentar_snap_suelo(self, hitbox_post: pygame.Rect, grupos: tuple[pygame.sprite.Group | None, ...]) -> None:
        margen_snap = 4
        for grupo in grupos:
            if not grupo:
                continue
            for sprite in grupo:
                if not hasattr(sprite, "obtener_recta_mascara"):
                    continue
                recta = sprite.obtener_recta_mascara()
                # Comprobar solape horizontal
                solapa_horizontal = not (hitbox_post.right <= recta.left or hitbox_post.left >= recta.right)
                if not solapa_horizontal:
                    continue
                # Comprobar que estamos justo encima dentro del margen
                delta = recta.top - hitbox_post.bottom
                if 0 <= delta <= margen_snap:
                    diferencia = hitbox_post.bottom - recta.top
                    self.rect.bottom -= diferencia
                    self.posicion.y = float(self.rect.y)
                    self.velocidad.y = 0.0
                    self.en_suelo = True
                    self.puede_saltar = True
                    self.tiempo_gracia_restante = self.tiempo_gracia_borde
                    return


    def _manejar_tecla_e(self, teclas: pygame.key.ScancodeWrapper) -> tuple[int, int] | None:
        if self.soldando:
            return None
        if not teclas[pygame.K_l] or self.cooldown_e > 0.0:
            return None
        
        if not self.en_suelo and not (self.sobre_plataforma or self.sobre_tuberia or self.sobre_extensor):
            return None
        
        if self.sobre_extensor and not self.tiene_extensor and self.recta_extensor_actual is not None:
            self.equipar_extensor(self.recta_extensor_actual)
            self.extensor_equipado = True
            self.cooldown_e = self.tiempo_cooldown_e
        elif self.tiene_extensor and (self.en_suelo or self.sobre_plataforma or self.sobre_tuberia):
            self.extensor_recien_creado = True
            self.cooldown_e = self.tiempo_cooldown_e
            return self.desequipar_extensor()
        
        return None

    def _escalar_fotograma(self, fotograma: pygame.Surface) -> pygame.Surface:
        return pygame.transform.scale(fotograma, (self.tamano_sprite, self.tamano_sprite))

    def _manejar_tecla_f(self, teclas: pygame.key.ScancodeWrapper, grupo_tuberias: pygame.sprite.Group | None) -> None:
        if self.soldando:
            return
        if self.tiene_extensor:
            return
        if grupo_tuberias is None:
            return
        if not self.sobre_tuberia:
            return
        if not teclas[pygame.K_k]:
            return
        tuberia_objetivo = self._buscar_tuberia_danada_cercana(grupo_tuberias)
        if tuberia_objetivo is None:
            return
        if not tuberia_objetivo.danada:
            return
        self.soldando = True
        self.tuberia_objetivo_soldar = tuberia_objetivo
        self.tiempo_soldadura_restante = self.tiempo_soldadura_total
        self.velocidad.x = 0.0
        self.velocidad.y = 0.0
        self._detener_sonido_movimiento()
        if self.animador_soldar:
            self.animador_actual = self.animador_soldar
            self.animador_soldar.reiniciar()
        self.gestor_sonido.reproducir_efecto(self.clave_soldadura_inicio, reiniciar=True)
        self.gestor_sonido.reproducir_efecto(self.clave_soldadura_bucle, loops=-1, reiniciar=True)

    def _buscar_tuberia_danada_cercana(self, grupo_tuberias: pygame.sprite.Group) -> Tuberia | None:
        if self.mascara.count() == 0:
            return None
        mejor_tuberia: Tuberia | None = None
        mejor_distancia = float("inf")
        radio_busqueda = 30
        
        centro_busqueda_x = self.rect.centerx
        centro_busqueda_y = self.rect.centery + 42
        
        self.area_busqueda_reparacion = pygame.Rect(
            centro_busqueda_x - radio_busqueda,
            centro_busqueda_y - radio_busqueda,
            radio_busqueda * 2,
            radio_busqueda * 2
        )
        self.tuberias_en_rango = []
        
        for tuberia in grupo_tuberias:
            if not hasattr(tuberia, "obtener_mascara") or not hasattr(tuberia, "obtener_recta_mascara"):
                continue
            if not getattr(tuberia, "danada", False):
                continue
            
            if hasattr(tuberia, "obtener_recta_reparacion"):
                recta_tuberia = tuberia.obtener_recta_reparacion()
            else:
                recta_tuberia = tuberia.obtener_recta_mascara()
            
            if self.area_busqueda_reparacion.colliderect(recta_tuberia):
                self.tuberias_en_rango.append(tuberia)  # type: ignore[arg-type]
                
                distancia_x = abs(recta_tuberia.centerx - centro_busqueda_x)
                distancia_y = abs(recta_tuberia.centery - centro_busqueda_y)
                distancia = distancia_x + distancia_y
                
                if distancia < mejor_distancia:
                    mejor_distancia = distancia
                    mejor_tuberia = tuberia  # type: ignore[assignment]
        
        return mejor_tuberia
