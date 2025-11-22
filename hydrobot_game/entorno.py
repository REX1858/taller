import pygame

from configuracion import ConfiguracionEscena
from extensor import Extensor
from gestor_sonido import GestorSonido
from plataforma import Plataforma
from player import Jugador


def limitar(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(valor, maximo))


def encontrar_plataforma_mas_baja(grupo_plataformas: pygame.sprite.Group, altura_mundo: int) -> Plataforma | None:
    if not grupo_plataformas:
        return None
    plataforma_mas_baja: Plataforma | None = None
    distancia_minima = float("inf")
    for plataforma in grupo_plataformas:
        if not isinstance(plataforma, Plataforma):
            continue
        distancia_al_suelo = altura_mundo - plataforma.rect.bottom
        if distancia_al_suelo < distancia_minima:
            distancia_minima = distancia_al_suelo
            plataforma_mas_baja = plataforma
    return plataforma_mas_baja


def manejar_extensor_soltado(jugador: Jugador, grupo_extensores: pygame.sprite.Group) -> None:
    if jugador.posicion_extensor_soltado is None:
        return
    centro_x, base_y = jugador.posicion_extensor_soltado
    gestor_sonido = getattr(jugador, "gestor_sonido", None)
    nuevo_extensor = Extensor((0, 0), gestor_sonido=gestor_sonido)
    nuevo_extensor.establecer_direccion(jugador.direccion_extensor_soltado)
    hitbox_temporal = nuevo_extensor.obtener_recta_mascara()
    desplazamiento_x = centro_x - hitbox_temporal.centerx
    desplazamiento_y = base_y - hitbox_temporal.bottom
    nuevo_extensor.rect.topleft = (nuevo_extensor.rect.x + desplazamiento_x, nuevo_extensor.rect.y + desplazamiento_y)
    nuevo_extensor.posicion.update(nuevo_extensor.rect.topleft)
    grupo_extensores.add(nuevo_extensor)


def crear_entorno(
    recta_pantalla: pygame.Rect,
    configuracion: ConfiguracionEscena,
    ruta_mapeado: str,
    gestor_sonido: GestorSonido,
    minimo_rotas: int = 0,
) -> tuple[
    Jugador,
    pygame.sprite.Group,
    pygame.sprite.Group,
    pygame.sprite.Group,
    pygame.sprite.Group,
    pygame.sprite.Group,
    pygame.Rect,
    int,
    int,
    pygame.math.Vector2,
    dict[str, object],
]:
    from generador_nivel import generar_nivel_desde_imagen

    grupo_plataformas, grupo_tuberias, altura_mundo, desplazamiento_x, ancho_mundo, datos_extra = generar_nivel_desde_imagen(
        ruta_mapeado,
        100,
        recta_pantalla.width,
        minimo_rotas,
        gestor_sonido=gestor_sonido,
    )
    grupo_particulas = pygame.sprite.Group()
    limites = pygame.Rect(desplazamiento_x, 0, ancho_mundo, altura_mundo)
    plataforma_spawn = encontrar_plataforma_mas_baja(grupo_plataformas, altura_mundo)
    if plataforma_spawn is not None:
        posicion_inicial_jugador = (int(plataforma_spawn.rect.centerx - 60), int(plataforma_spawn.rect.top - 120))
    else:
        posicion_inicial_jugador = (recta_pantalla.centerx - 25, altura_mundo - 120)
    jugador = Jugador(posicion_inicial_jugador, gestor_sonido)
    grupo_sprites = pygame.sprite.Group()
    grupo_sprites.add(jugador)
    grupo_extensores = pygame.sprite.Group()
    desplazamiento_camara = pygame.math.Vector2(0.0, 0.0)
    max_scroll_y = altura_mundo - recta_pantalla.height
    if max_scroll_y > 0:
        desplazamiento_camara.y = limitar(jugador.rect.centery - recta_pantalla.height / 2, 0.0, max_scroll_y)
    mundo_izquierda = limites.left
    mundo_ancho = limites.width
    mundo_derecha = limites.right
    max_scroll_x = mundo_derecha - recta_pantalla.width
    if max_scroll_x <= mundo_izquierda:
        centro_mundo_x = mundo_izquierda + mundo_ancho / 2
        desplazamiento_camara.x = max(0.0, centro_mundo_x - recta_pantalla.width / 2)
    else:
        desplazamiento_camara.x = limitar(jugador.rect.centerx - recta_pantalla.width / 2, mundo_izquierda, max_scroll_x)
    return (
        jugador,
        grupo_sprites,
        grupo_extensores,
        grupo_plataformas,
        grupo_tuberias,
        grupo_particulas,
        limites,
        altura_mundo,
        ancho_mundo,
        desplazamiento_camara,
        datos_extra,
    )
