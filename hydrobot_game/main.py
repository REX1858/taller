import sys

import pygame

from boton import Boton
from configuracion import (
    CONFIGURACION_TUTORIAL,
    CONFIGURACIONES_ESCENA,
    ConfiguracionEscena,
    RUTA_BOTON_MENU,
    RUTA_FONDO_MOSAICO,
    RUTA_MAPEADO_ESCENA1,
    RUTA_MAPEADO_ESCENA2,
    RUTA_MAPEADO_ESCENA3,
    RUTA_MAPEADO_TUTORIAL,
    RUTA_MUSICA_ESCENA1,
    RUTA_MUSICA_ESCENA2,
    RUTA_MUSICA_ESCENA3,
    RUTA_MUSICA_MENU,
    RUTA_NPC_TUTORIAL,
    RUTA_SONIDO_FELICIDADES,
    TAMANO_VENTANA,
)
from entorno import crear_entorno, limitar, manejar_extensor_soltado
from gestor_sonido import GestorSonido
from minimapa import MiniMapa
from npc_tutorial import NPCTutorial
from player import Jugador


def crear_botones_menu(recta_pantalla: pygame.Rect, textura: pygame.Surface | None) -> dict[str, Boton]:
    ancho = 280
    alto = 76
    separacion = 26
    centro_x = recta_pantalla.centerx
    total_alto = alto * 3 + separacion * 2
    inicio_y = recta_pantalla.centery - total_alto // 2
    return {
        "jugar": Boton(
            "Jugar",
            (centro_x, inicio_y + alto // 2),
            (ancho, alto),
            textura,
        ),
        "opciones": Boton(
            "Opciones",
            (centro_x, inicio_y + alto // 2 + alto + separacion),
            (ancho, alto),
            textura,
        ),
        "salir": Boton(
            "Salir",
            (centro_x, inicio_y + alto // 2 + 2 * (alto + separacion)),
            (ancho, alto),
            textura,
        ),
    }


def crear_botones_escenas(recta_pantalla: pygame.Rect, textura: pygame.Surface | None) -> dict[str, Boton]:
    ancho = 220
    alto = 80
    espacio_horizontal = 36
    y_superior = recta_pantalla.centery - alto - 30
    y_inferior = recta_pantalla.centery + alto + 30
    inicio_x = recta_pantalla.centerx - ((ancho * 3) + (espacio_horizontal * 2)) // 2
    botones: dict[str, Boton] = {}
    for indice, etiqueta in enumerate(["1", "2", "3"]):
        centro = (
            int(inicio_x + indice * (ancho + espacio_horizontal) + ancho // 2),
            y_superior,
        )
        botones[etiqueta] = Boton(etiqueta, centro, (ancho, alto), textura)
    botones["tutorial"] = Boton(
        "Tutorial",
        (recta_pantalla.centerx, y_inferior),
        (300, 80),
        textura,
    )
    botones["volver"] = Boton(
        "Volver",
        (recta_pantalla.centerx, recta_pantalla.bottom - 90),
        (260, 72),
        textura,
    )
    return botones


def crear_botones_opciones(recta_pantalla: pygame.Rect, textura: pygame.Surface | None) -> dict[str, Boton]:
    ancho = 200
    alto = 68
    separacion_vertical = 34
    centro_x = recta_pantalla.centerx
    fila_1_y = recta_pantalla.top + 260
    fila_2_y = fila_1_y + alto + separacion_vertical
    fila_3_y = fila_2_y + alto + separacion_vertical
    offset_horizontal = 150
    botones: dict[str, Boton] = {
        "volumen_musica_menos": Boton("-", (centro_x - offset_horizontal, fila_1_y), (ancho, alto), textura),
        "volumen_musica_mas": Boton("+", (centro_x + offset_horizontal, fila_1_y), (ancho, alto), textura),
        "volumen_efectos_menos": Boton("-", (centro_x - offset_horizontal, fila_2_y), (ancho, alto), textura),
        "volumen_efectos_mas": Boton("+", (centro_x + offset_horizontal, fila_2_y), (ancho, alto), textura),
        "musica_toggle": Boton("Musica SI/NO", (centro_x, fila_3_y), (ancho + 80, alto), textura),
        "volver": Boton("Volver", (centro_x, recta_pantalla.bottom - 90), (280, 76), textura),
    }
    return botones


def ejecutar_juego() -> None:
    pygame.init()
    pygame.display.set_caption("Demostracion Hydrobot")

    pantalla = pygame.display.set_mode(TAMANO_VENTANA)
    recta_pantalla = pantalla.get_rect()
    reloj = pygame.time.Clock()
    fuente_titulo = pygame.font.Font(None, 74)
    fuente_mediana = pygame.font.Font(None, 48)
    fuente_pequena = pygame.font.Font(None, 32)

    gestor = GestorSonido(RUTA_MUSICA_MENU)
    
    try:
        imagen_fondo_base = pygame.image.load(RUTA_FONDO_MOSAICO).convert()
        ancho_original = imagen_fondo_base.get_width()
        alto_original = imagen_fondo_base.get_height()
        nuevo_ancho = int(ancho_original * 10)
        nuevo_alto = int(alto_original * 10)
        imagen_fondo_base = pygame.transform.scale(imagen_fondo_base, (nuevo_ancho, nuevo_alto))
    except pygame.error:
        imagen_fondo_base = None

    try:
        textura_boton_menu = pygame.image.load(RUTA_BOTON_MENU).convert_alpha()
    except pygame.error:
        textura_boton_menu = None
    
    configuracion_actual: ConfiguracionEscena = CONFIGURACIONES_ESCENA["1"]
    escena_actual = ""
    
    jugador: Jugador | None = None
    grupo_sprites: pygame.sprite.Group | None = None
    grupo_extensores: pygame.sprite.Group | None = None
    grupo_plataformas: pygame.sprite.Group | None = None
    grupo_tuberias: pygame.sprite.Group | None = None
    grupo_particulas: pygame.sprite.Group | None = None
    limites_movimiento: pygame.Rect | None = None
    altura_mundo = 0
    desplazamiento_camara = pygame.math.Vector2(0, 0)
    superficie_fondo_nivel: pygame.Surface | None = None
    minimapa: MiniMapa | None = None

    estado = "menu"
    estado_anterior = ""
    botones_menu = crear_botones_menu(recta_pantalla, textura_boton_menu)
    botones_escenas = crear_botones_escenas(recta_pantalla, textura_boton_menu)
    botones_opciones = crear_botones_opciones(recta_pantalla, textura_boton_menu)
    estados_con_musica = {"menu", "seleccion_escena", "opciones"}
    recta_meta_tutorial: pygame.Rect | None = None
    tuberias_verticales_tutorial: list[pygame.sprite.Sprite] = []
    tuberias_tutorial_reparadas = False
    caida_tuberias_iniciada = False
    npc_tutorial = NPCTutorial(RUTA_NPC_TUTORIAL)
    npc_texto_superficie: pygame.Surface | None = None
    
    def construir_cuadro_dialogo(texto: str) -> pygame.Surface:
        superficie_texto = fuente_pequena.render(texto, True, (235, 240, 250))
        margen = 12
        ancho = superficie_texto.get_width() + margen * 2
        alto = superficie_texto.get_height() + margen * 2
        superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        superficie.fill((10, 18, 28, 215))
        superficie.blit(superficie_texto, (margen, margen))
        return superficie

    def actualizar_cuadro_dialogo_npc() -> None:
        nonlocal npc_texto_superficie
        dialogo_actual = npc_tutorial.obtener_dialogo_actual()
        if dialogo_actual is None:
            npc_texto_superficie = None
            return
        npc_texto_superficie = construir_cuadro_dialogo(dialogo_actual)

    def avanzar_dialogo_npc() -> None:
        npc_tutorial.avanzar_dialogo()
        actualizar_cuadro_dialogo_npc()

    def cargar_escena(etiqueta: str) -> bool:
        nonlocal configuracion_actual, escena_actual, jugador, grupo_sprites, grupo_extensores, grupo_plataformas, grupo_tuberias
        nonlocal grupo_particulas, limites_movimiento, altura_mundo, desplazamiento_camara, superficie_fondo_nivel, minimapa
        nonlocal estado, estado_anterior, tuberias_tutorial_reparadas, caida_tuberias_iniciada, recta_meta_tutorial, tuberias_verticales_tutorial
        nonlocal npc_texto_superficie
        nonlocal mostrar_minimapa

        if etiqueta == "tutorial":
            configuracion_actual = CONFIGURACION_TUTORIAL
            ruta_mapeado_local = RUTA_MAPEADO_TUTORIAL
        elif etiqueta in CONFIGURACIONES_ESCENA:
            configuracion_actual = CONFIGURACIONES_ESCENA[etiqueta]
            if etiqueta == "1":
                ruta_mapeado_local = RUTA_MAPEADO_ESCENA1
            elif etiqueta == "2":
                ruta_mapeado_local = RUTA_MAPEADO_ESCENA2
            else:
                ruta_mapeado_local = RUTA_MAPEADO_ESCENA3
        else:
            return False

        escena_actual = etiqueta
        minimo_rotas = 3 if etiqueta == "1" else 0
        (
            jugador,
            grupo_sprites,
            grupo_extensores,
            grupo_plataformas,
            grupo_tuberias,
            grupo_particulas,
            limites_movimiento,
            altura_mundo,
            _ancho_mundo,
            desplazamiento_camara,
            datos_nivel,
        ) = crear_entorno(
            recta_pantalla,
            configuracion_actual,
            ruta_mapeado_local,
            gestor,
            minimo_rotas,
        )

        minimapa = MiniMapa()
        if limites_movimiento is not None:
            minimapa.establecer_limites(limites_movimiento)

        if imagen_fondo_base and altura_mundo > 0:
            ancho_superficie = max(recta_pantalla.width, int(limites_movimiento.right)) if limites_movimiento else recta_pantalla.width
            alto_superficie = max(recta_pantalla.height, altura_mundo)
            superficie_fondo_nivel = pygame.Surface((ancho_superficie, alto_superficie)).convert()
            ancho_tile_f = imagen_fondo_base.get_width()
            alto_tile_f = imagen_fondo_base.get_height()
            for y_f in range(0, alto_superficie, alto_tile_f):
                for x_f in range(0, ancho_superficie, ancho_tile_f):
                    superficie_fondo_nivel.blit(imagen_fondo_base, (x_f, y_f))
        else:
            superficie_fondo_nivel = None

        estado = "jugando"
        estado_anterior = "seleccion_escena"

        tuberias_tutorial_reparadas = False
        caida_tuberias_iniciada = False
        recta_meta_tutorial = None
        tuberias_verticales_tutorial = []
        npc_tutorial.reiniciar()
        npc_texto_superficie = None

        if escena_actual == "tutorial":
            meta_posible = datos_nivel.get("recta_meta") if isinstance(datos_nivel, dict) else None
            if isinstance(meta_posible, pygame.Rect):
                recta_meta_tutorial = meta_posible
            lista_posible = datos_nivel.get("tuberias_verticales") if isinstance(datos_nivel, dict) else None
            if isinstance(lista_posible, list):
                if grupo_tuberias is not None:
                    tuberias_verticales_tutorial = [t for t in lista_posible if t in grupo_tuberias]
                else:
                    tuberias_verticales_tutorial = list(lista_posible)
            if recta_meta_tutorial is not None:
                npc_tutorial.cargar(recta_meta_tutorial)
            npc_tutorial.asignar_dialogos([
                "Interactuar: K",
                "Mover: WASD",
                "Correr: Shift",
                "Montura: L para bajar",
                "Llamar extensor: L cuando eres mini",
            ])
            actualizar_cuadro_dialogo_npc()
            mostrar_minimapa = False
        else:
            npc_texto_superficie = None

        if escena_actual == "1":
            gestor.reproducir_musica(RUTA_MUSICA_ESCENA1)
        elif escena_actual == "2":
            gestor.reproducir_musica(RUTA_MUSICA_ESCENA2)
        elif escena_actual == "3":
            gestor.reproducir_musica(RUTA_MUSICA_ESCENA3)
        else:
            gestor.detener_musica()

        if escena_actual != "tutorial":
            mostrar_minimapa = True

        return True
    mostrar_hitboxes = False
    mostrar_minimapa = True

    # Tiempo y finalizacion de nivel
    tiempo_inicio_nivel = 0.0
    tiempo_total_nivel = 0.0
    sonido_felicidades_reproducido = False

    juego_activo = True
    while juego_activo:
        dt = reloj.tick(60) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                juego_activo = False
            elif estado == "menu":
                if botones_menu["jugar"].fue_clic(evento):
                    estado = "seleccion_escena"
                elif botones_menu["opciones"].fue_clic(evento):
                    estado = "opciones"
                elif botones_menu["salir"].fue_clic(evento):
                    juego_activo = False
            elif estado == "seleccion_escena":
                if botones_escenas["volver"].fue_clic(evento):
                    estado = "menu"
                else:
                    for etiqueta in ["1", "2", "3", "tutorial"]:
                        if botones_escenas[etiqueta].fue_clic(evento):
                            if cargar_escena(etiqueta):
                                break
            elif estado == "opciones":
                if botones_opciones["volver"].fue_clic(evento):
                    estado = "menu"
                elif botones_opciones["volumen_musica_menos"].fue_clic(evento):
                    gestor.ajustar_volumen_musica(-0.1)
                elif botones_opciones["volumen_musica_mas"].fue_clic(evento):
                    gestor.ajustar_volumen_musica(0.1)
                elif botones_opciones["volumen_efectos_menos"].fue_clic(evento):
                    gestor.ajustar_volumen_efectos(-0.1)
                elif botones_opciones["volumen_efectos_mas"].fue_clic(evento):
                    gestor.ajustar_volumen_efectos(0.1)
                elif botones_opciones["musica_toggle"].fue_clic(evento):
                    gestor.alternar_musica()
            elif estado == "jugando":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    estado = "menu"
                    escena_actual = ""
                    minimapa = None
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_F1:
                    mostrar_hitboxes = not mostrar_hitboxes
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_l and grupo_extensores is not None and jugador is not None:
                    for extensor in (grupo_extensores or []):
                        if hasattr(extensor, "ordenar_ir_a_jugador"):
                            extensor.ordenar_ir_a_jugador(jugador)
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_k and grupo_extensores is not None and jugador is not None:
                    for extensor in (grupo_extensores or []):
                        if hasattr(extensor, "ordenar_reparar"):
                            extensor.ordenar_reparar(jugador)
                    if (
                        escena_actual == "tutorial"
                        and npc_tutorial.esta_disponible()
                        and npc_tutorial.en_rango(jugador.rect)
                    ):
                        avanzar_dialogo_npc()
                    if (
                        escena_actual == "tutorial"
                        and tuberias_tutorial_reparadas
                        and recta_meta_tutorial is not None
                        and jugador.rect.colliderect(recta_meta_tutorial)
                        and estado == "jugando"
                        and getattr(jugador, "tiene_extensor", False)
                        and not any(getattr(t, "en_caida", False) for t in tuberias_verticales_tutorial)
                    ):
                        tiempo_total_nivel = max(0.0, (pygame.time.get_ticks() / 1000.0) - tiempo_inicio_nivel)
                        if not sonido_felicidades_reproducido:
                            gestor.reproducir_efecto_puntual(RUTA_SONIDO_FELICIDADES)
                            sonido_felicidades_reproducido = True
                        estado = "nivel_completado"
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_m:
                    mostrar_minimapa = not mostrar_minimapa
                elif evento.type == pygame.KEYDOWN and evento.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    if minimapa is not None:
                        minimapa.ajustar_zoom(0.1)
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_KP_MINUS:
                    if minimapa is not None:
                        minimapa.ajustar_zoom(-0.1)
            elif estado == "nivel_completado":
                if evento.type == pygame.KEYDOWN and (evento.key == pygame.K_RETURN or evento.key == pygame.K_ESCAPE):
                    estado = "menu"
                    escena_actual = ""
                    minimapa = None
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    estado = "menu"
                    escena_actual = ""
                    minimapa = None

        if estado == "jugando" and escena_actual == "1":
            if gestor.musica_habilitada and not gestor.musica_sonando:
                gestor.reproducir_musica(RUTA_MUSICA_ESCENA1)
        elif estado == "jugando" and escena_actual == "2":
            if gestor.musica_habilitada and not gestor.musica_sonando:
                gestor.reproducir_musica(RUTA_MUSICA_ESCENA2)
        elif estado == "jugando" and escena_actual == "3":
            if gestor.musica_habilitada and not gestor.musica_sonando:
                gestor.reproducir_musica(RUTA_MUSICA_ESCENA3)
        else:
            gestor.manejar_estado_musica(estado, estados_con_musica)

        if estado == "jugando" and superficie_fondo_nivel is not None:
            ancho_fondo = superficie_fondo_nivel.get_width()
            alto_fondo = superficie_fondo_nivel.get_height()
            x_inicio = 0
            y_inicio = 0
            if ancho_fondo > recta_pantalla.width:
                x_inicio = int(desplazamiento_camara.x)
                x_max = ancho_fondo - recta_pantalla.width
                x_inicio = max(0, min(x_inicio, x_max))
            if alto_fondo > recta_pantalla.height:
                y_inicio = int(desplazamiento_camara.y)
                y_max = alto_fondo - recta_pantalla.height
                y_inicio = max(0, min(y_inicio, y_max))
            region = pygame.Rect(x_inicio, y_inicio, min(recta_pantalla.width, ancho_fondo), min(recta_pantalla.height, alto_fondo))
            pantalla.blit(superficie_fondo_nivel.subsurface(region), (0, 0))
        else:
            pantalla.fill(configuracion_actual["color_fondo"])

        # Transicion y temporizador de inicio del nivel
        if estado_anterior != estado:
            if estado == "jugando":
                tiempo_inicio_nivel = pygame.time.get_ticks() / 1000.0
                tiempo_total_nivel = 0.0
                sonido_felicidades_reproducido = False
            estado_anterior = estado

        if estado == "menu":
            titulo = fuente_titulo.render("Hydrobot", True, (235, 235, 240))
            pantalla.blit(titulo, titulo.get_rect(center=(recta_pantalla.centerx, recta_pantalla.top + 120)))
            for boton in botones_menu.values():
                boton.dibujar(pantalla, fuente_mediana)
        elif estado == "seleccion_escena":
            for clave in ["1", "2", "3"]:
                botones_escenas[clave].dibujar(pantalla, fuente_mediana)
            botones_escenas["tutorial"].dibujar(pantalla, fuente_mediana)
            botones_escenas["volver"].dibujar(pantalla, fuente_pequena)
        elif estado == "opciones":
            texto = fuente_titulo.render("Opciones", True, (235, 235, 240))
            pantalla.blit(texto, texto.get_rect(center=(recta_pantalla.centerx, recta_pantalla.top + 140)))
            alto_boton = 68
            separacion_vertical = 34
            fila_1_y = recta_pantalla.top + 260
            fila_2_y = fila_1_y + alto_boton + separacion_vertical
            fila_3_y = fila_2_y + alto_boton + separacion_vertical

            descripcion_musica = fuente_pequena.render(f"Vol musica: {gestor.obtener_volumen_musica()}", True, (220, 220, 230))
            descripcion_efectos = fuente_pequena.render(f"Vol efectos: {gestor.obtener_volumen_efectos()}", True, (220, 220, 230))
            descripcion_toggle = fuente_pequena.render(f"Musica: {gestor.obtener_estado_musica()}", True, (220, 220, 230))
            pantalla.blit(descripcion_musica, descripcion_musica.get_rect(center=(recta_pantalla.centerx, fila_1_y - alto_boton // 2 - 24)))
            pantalla.blit(descripcion_efectos, descripcion_efectos.get_rect(center=(recta_pantalla.centerx, fila_2_y - alto_boton // 2 - 24)))
            pantalla.blit(descripcion_toggle, descripcion_toggle.get_rect(center=(recta_pantalla.centerx, fila_3_y - alto_boton // 2 - 24)))
            for boton in botones_opciones.values():
                boton.dibujar(pantalla, fuente_mediana)
        elif estado == "jugando" and grupo_sprites and limites_movimiento and jugador and grupo_extensores is not None:
            teclas = pygame.key.get_pressed()
            
            jugador.update(teclas, dt, limites_movimiento, grupo_extensores, grupo_plataformas, grupo_tuberias)
            
            mundo_izquierda = limites_movimiento.left
            mundo_ancho = limites_movimiento.width
            mundo_derecha = limites_movimiento.right
            max_scroll_x = mundo_derecha - recta_pantalla.width
            if max_scroll_x <= mundo_izquierda:
                centro_mundo_x = mundo_izquierda + mundo_ancho / 2
                desplazamiento_camara.x = max(0.0, centro_mundo_x - recta_pantalla.width / 2)
            else:
                objetivo_x = jugador.rect.centerx - recta_pantalla.width / 2
                desplazamiento_camara.x = limitar(objetivo_x, mundo_izquierda, max_scroll_x)

            max_scroll_y = altura_mundo - recta_pantalla.height
            if max_scroll_y <= 0:
                desplazamiento_camara.y = 0.0
            else:
                objetivo_y = jugador.rect.centery - recta_pantalla.height / 2
                desplazamiento_camara.y = limitar(objetivo_y, 0.0, max_scroll_y)
            
            manejar_extensor_soltado(jugador, grupo_extensores)
            
            if grupo_tuberias:
                grupo_tuberias.update(dt, grupo_particulas)
            if grupo_particulas:
                grupo_particulas.update(dt)
            
            if grupo_extensores:
                grupo_extensores.update(dt, grupo_plataformas, limites_movimiento)
            
            offset_x = desplazamiento_camara.x
            offset_y = desplazamiento_camara.y
            if grupo_plataformas:
                for plataforma in grupo_plataformas:
                    pantalla.blit(
                        plataforma.image,
                        (int(plataforma.rect.x - offset_x), int(plataforma.rect.y - offset_y)),
                    )
            if grupo_tuberias:
                for tuberia in grupo_tuberias:
                    pantalla.blit(
                        tuberia.image,
                        (int(tuberia.rect.x - offset_x), int(tuberia.rect.y - offset_y)),
                    )
                    if hasattr(tuberia, "obtener_decal"):
                        resultado = tuberia.obtener_decal()
                        if resultado is not None:
                            decal_superficie, decal_rect = resultado
                            pantalla.blit(
                                decal_superficie,
                                (int(decal_rect.x - offset_x), int(decal_rect.y - offset_y)),
                            )
            if grupo_particulas:
                for particula in grupo_particulas:
                    pantalla.blit(
                        particula.image,
                        (int(particula.rect.x - offset_x), int(particula.rect.y - offset_y)),
                    )
            if grupo_extensores:
                for extensor in grupo_extensores:
                    pantalla.blit(
                        extensor.image,
                        (int(extensor.rect.x - offset_x), int(extensor.rect.y - offset_y)),
                    )
            
            recta_npc_pantalla: pygame.Rect | None = None
            if escena_actual == "tutorial" and jugador is not None:
                npc_tutorial.actualizar_orientacion(jugador.rect)
                recta_npc_pantalla = npc_tutorial.dibujar(
                    pantalla,
                    (int(offset_x), int(offset_y)),
                )
                if recta_npc_pantalla is not None and npc_texto_superficie is not None:
                    posicion_texto = pygame.Rect(0, 0, npc_texto_superficie.get_width(), npc_texto_superficie.get_height())
                    posicion_texto.midbottom = (
                        recta_npc_pantalla.centerx,
                        recta_npc_pantalla.top - 12,
                    )
                    pantalla.blit(npc_texto_superficie, posicion_texto.topleft)

            if jugador.image:
                pantalla.blit(
                    jugador.image,
                    (int(jugador.rect.x - offset_x), int(jugador.rect.y - offset_y)),
                )
            
            if mostrar_hitboxes:
                if jugador.area_busqueda_reparacion:
                    area_pantalla = pygame.Rect(
                        int(jugador.area_busqueda_reparacion.x - offset_x),
                        int(jugador.area_busqueda_reparacion.y - offset_y),
                        jugador.area_busqueda_reparacion.width,
                        jugador.area_busqueda_reparacion.height
                    )
                    pygame.draw.circle(pantalla, (128, 0, 128), area_pantalla.center, jugador.area_busqueda_reparacion.width // 2, 2)
                
                if jugador.tuberias_en_rango:
                    for tuberia in jugador.tuberias_en_rango:
                        if hasattr(tuberia, "obtener_recta_mascara"):
                            hitbox = tuberia.obtener_recta_mascara()
                            hitbox_pantalla = pygame.Rect(
                                int(hitbox.x - offset_x),
                                int(hitbox.y - offset_y),
                                hitbox.width,
                                hitbox.height,
                            )
                            pygame.draw.rect(pantalla, (255, 255, 255), hitbox_pantalla, 3)
                
                if jugador.tuberia_objetivo_soldar:
                    if hasattr(jugador.tuberia_objetivo_soldar, "obtener_recta_mascara"):
                        hitbox = jugador.tuberia_objetivo_soldar.obtener_recta_mascara()
                        hitbox_pantalla = pygame.Rect(
                            int(hitbox.x - offset_x),
                            int(hitbox.y - offset_y),
                            hitbox.width,
                            hitbox.height,
                        )
                        pygame.draw.rect(pantalla, (0, 255, 0), hitbox_pantalla, 4)
                        pygame.draw.line(pantalla, (0, 255, 0), 
                                       (int(jugador.rect.centerx - offset_x), int(jugador.rect.centery - offset_y)),
                                       (int(hitbox.centerx - offset_x), int(hitbox.centery - offset_y)), 3)
                
                if grupo_plataformas:
                    for plataforma in grupo_plataformas:
                        if hasattr(plataforma, "obtener_recta_mascara"):
                            hitbox = plataforma.obtener_recta_mascara()
                            hitbox_pantalla = pygame.Rect(
                                int(hitbox.x - offset_x),
                                int(hitbox.y - offset_y),
                                hitbox.width,
                                hitbox.height,
                            )
                            pygame.draw.rect(pantalla, (0, 255, 0), hitbox_pantalla, 2)
                            if hasattr(plataforma, "mascara"):
                                mascara = plataforma.mascara
                                superficie_mascara = mascara.to_surface(setcolor=(0, 255, 0, 80), unsetcolor=(0, 0, 0, 0))
                                pantalla.blit(
                                    superficie_mascara,
                                    (int(plataforma.rect.x - offset_x), int(plataforma.rect.y - offset_y)),
                                )
                
                if grupo_tuberias:
                    for tuberia in grupo_tuberias:
                        if hasattr(tuberia, "obtener_recta_mascara"):
                            hitbox = tuberia.obtener_recta_mascara()
                            hitbox_pantalla = pygame.Rect(
                                int(hitbox.x - offset_x),
                                int(hitbox.y - offset_y),
                                hitbox.width,
                                hitbox.height,
                            )
                            color_tuberia = (255, 165, 0) if getattr(tuberia, "danada", False) else (0, 255, 255)
                            pygame.draw.rect(pantalla, color_tuberia, hitbox_pantalla, 2)
                            if hasattr(tuberia, "mascara"):
                                mascara = tuberia.mascara
                                color_mascara = (255, 165, 0, 80) if getattr(tuberia, "danada", False) else (0, 255, 255, 80)
                                superficie_mascara = mascara.to_surface(setcolor=color_mascara, unsetcolor=(0, 0, 0, 0))
                                pantalla.blit(
                                    superficie_mascara,
                                    (int(tuberia.rect.x - offset_x), int(tuberia.rect.y - offset_y)),
                                )
                
                if grupo_extensores:
                    for extensor in grupo_extensores:
                        if hasattr(extensor, "obtener_recta_mascara"):
                            hitbox = extensor.obtener_recta_mascara()
                            hitbox_pantalla = pygame.Rect(
                                int(hitbox.x - offset_x),
                                int(hitbox.y - offset_y),
                                hitbox.width,
                                hitbox.height,
                            )
                            pygame.draw.rect(pantalla, (255, 255, 0), hitbox_pantalla, 2)
                            if hasattr(extensor, "mascara"):
                                mascara = extensor.mascara
                                superficie_mascara = mascara.to_surface(setcolor=(255, 255, 0, 80), unsetcolor=(0, 0, 0, 0))
                                pantalla.blit(
                                    superficie_mascara,
                                    (int(extensor.rect.x - offset_x), int(extensor.rect.y - offset_y)),
                                )
                
                if grupo_particulas:
                    for particula in grupo_particulas:
                        hitbox_particula = particula.rect
                        hitbox_pantalla = pygame.Rect(
                            int(hitbox_particula.x - offset_x),
                            int(hitbox_particula.y - offset_y),
                            hitbox_particula.width,
                            hitbox_particula.height,
                        )
                        pygame.draw.rect(pantalla, (255, 0, 255), hitbox_pantalla, 1)
                
                hitbox_jugador = jugador.obtener_recta_mascara()
                hitbox_pantalla = pygame.Rect(
                    int(hitbox_jugador.x - offset_x),
                    int(hitbox_jugador.y - offset_y),
                    hitbox_jugador.width,
                    hitbox_jugador.height,
                )
                pygame.draw.rect(pantalla, (255, 0, 0), hitbox_pantalla, 2)
                
                mascara_jugador = jugador.mascara
                superficie_mascara_jugador = mascara_jugador.to_surface(setcolor=(255, 0, 0, 100), unsetcolor=(0, 0, 0, 0))
                pantalla.blit(
                    superficie_mascara_jugador,
                    (int(jugador.rect.x - offset_x), int(jugador.rect.y - offset_y)),
                )

            if mostrar_minimapa and minimapa is not None:
                minimapa.dibujar(
                    pantalla,
                    jugador,
                    grupo_plataformas,
                    grupo_tuberias,
                    grupo_extensores,
                    desplazamiento_camara,
                    recta_pantalla,
                )

            # Comprobacion de nivel completado
            if grupo_tuberias is not None:
                quedan_danadas = any(getattr(t, "danada", False) for t in grupo_tuberias)
                if escena_actual == "tutorial":
                    if quedan_danadas:
                        tuberias_tutorial_reparadas = False
                    else:
                        if not tuberias_tutorial_reparadas:
                            tuberias_tutorial_reparadas = True
                        if not caida_tuberias_iniciada:
                            for tuberia in tuberias_verticales_tutorial:
                                metodo_caida = getattr(tuberia, "iniciar_caida", None)
                                if callable(metodo_caida):
                                    metodo_caida(altura_mundo)
                            caida_tuberias_iniciada = True
                elif not quedan_danadas:
                    tiempo_total_nivel = max(0.0, (pygame.time.get_ticks() / 1000.0) - tiempo_inicio_nivel)
                    if not sonido_felicidades_reproducido:
                        gestor.reproducir_efecto_puntual(RUTA_SONIDO_FELICIDADES)
                        sonido_felicidades_reproducido = True
                    estado = "nivel_completado"
        elif estado == "nivel_completado":
            # Fondo atenuado
            overlay = pygame.Surface(TAMANO_VENTANA, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            pantalla.blit(overlay, (0, 0))
            # Cartel
            texto_titulo = fuente_titulo.render("¡Felicidades!", True, (235, 235, 240))
            pantalla.blit(texto_titulo, texto_titulo.get_rect(center=(recta_pantalla.centerx, recta_pantalla.centery - 60)))
            minutos = int(tiempo_total_nivel // 60)
            segundos = tiempo_total_nivel % 60
            texto_tiempo = fuente_mediana.render(f"Tiempo: {minutos} min {segundos:.2f} s", True, (220, 220, 230))
            pantalla.blit(texto_tiempo, texto_tiempo.get_rect(center=(recta_pantalla.centerx, recta_pantalla.centery + 10)))
            texto_aviso = fuente_pequena.render("Enter o clic para volver al menu", True, (200, 200, 210))
            pantalla.blit(texto_aviso, texto_aviso.get_rect(center=(recta_pantalla.centerx, recta_pantalla.centery + 60)))

        pygame.display.flip()

    gestor.limpiar()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    ejecutar_juego()
