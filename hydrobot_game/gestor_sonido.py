import pygame
from typing import Optional


class GestorSonido:
    def __init__(self, ruta_musica_menu: str) -> None:
        self.ruta_musica_menu = ruta_musica_menu
        self.ruta_musica_actual: str | None = None
        self.volumen_musica = 0.4
        self.volumen_efectos = 0.6
        self.musica_habilitada = True
        self.musica_sonando = False
        self._efectos: dict[str, pygame.mixer.Sound] = {}
        self._efectos_puntuales: dict[str, pygame.mixer.Sound] = {}
        self._config_efectos: dict[str, dict[str, Optional[float | int | str]]] = {}
        self._canales_reservados: dict[str, Optional[pygame.mixer.Channel]] = {}
        self._canales_activos: dict[str, Optional[pygame.mixer.Channel]] = {}
        self._inicializar_mixer()

    def _inicializar_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
            try:
                pygame.mixer.set_reserved(4)
            except pygame.error:
                pass
        except pygame.error as error:
            print(f"Error al inicializar mixer: {error}")

    def cargar_musica(self, ruta: str) -> None:
        if self.ruta_musica_actual == ruta:
            return
        try:
            self.detener_musica()
            pygame.mixer.music.load(ruta)
            self.ruta_musica_actual = ruta
            self.musica_sonando = False
        except pygame.error as error:
            print(f"Error al cargar musica: {error}")

    def reproducir_musica(self, ruta: str | None = None) -> None:
        if ruta:
            self.cargar_musica(ruta)
        if self.musica_habilitada and not self.musica_sonando:
            try:
                pygame.mixer.music.set_volume(self.volumen_musica)
                pygame.mixer.music.play(-1)
                self.musica_sonando = True
            except pygame.error as error:
                print(f"Error al reproducir musica: {error}")

    def reproducir_musica_menu(self) -> None:
        self.reproducir_musica(self.ruta_musica_menu)

    def detener_musica(self) -> None:
        if self.musica_sonando:
            try:
                pygame.mixer.music.stop()
                self.musica_sonando = False
            except pygame.error as error:
                print(f"Error al detener musica: {error}")

    def alternar_musica(self) -> bool:
        self.musica_habilitada = not self.musica_habilitada
        if self.musica_habilitada:
            self.reproducir_musica_menu()
        else:
            self.detener_musica()
        return self.musica_habilitada

    def ajustar_volumen_musica(self, cantidad: float) -> float:
        self.volumen_musica = max(0.0, min(1.0, self.volumen_musica + cantidad))
        if self.musica_sonando:
            try:
                pygame.mixer.music.set_volume(self.volumen_musica)
            except pygame.error as error:
                print(f"Error al ajustar volumen: {error}")
        return round(self.volumen_musica, 2)

    def ajustar_volumen_efectos(self, cantidad: float) -> float:
        self.volumen_efectos = max(0.0, min(1.0, self.volumen_efectos + cantidad))
        return round(self.volumen_efectos, 2)

    def manejar_estado_musica(self, estado: str, estados_con_musica: set[str]) -> None:
        if estado in estados_con_musica and self.musica_habilitada:
            self.reproducir_musica_menu()
        else:
            self.detener_musica()

    def obtener_volumen_musica(self) -> float:
        return round(self.volumen_musica, 1)

    def obtener_volumen_efectos(self) -> float:
        return round(self.volumen_efectos, 1)

    def obtener_estado_musica(self) -> str:
        return "SI" if self.musica_habilitada else "NO"

    def registrar_efecto(self, clave: str, ruta: str, canal: int | None = None, volumen: float = 1.0) -> None:
        volumen_clamp = max(0.0, min(1.0, volumen))
        self._config_efectos[clave] = {"ruta": ruta, "canal": canal, "volumen": volumen_clamp}
        self._efectos.pop(clave, None)
        if canal is not None:
            try:
                self._canales_reservados[clave] = pygame.mixer.Channel(canal)
            except pygame.error:
                self._canales_reservados[clave] = None

    def actualizar_ruta_efecto(self, clave: str, ruta: str) -> None:
        if clave not in self._config_efectos:
            self.registrar_efecto(clave, ruta)
            return
        self._config_efectos[clave]["ruta"] = ruta
        self._efectos.pop(clave, None)

    def actualizar_volumen_efecto(self, clave: str, volumen: float) -> None:
        if clave not in self._config_efectos:
            return
        self._config_efectos[clave]["volumen"] = max(0.0, min(1.0, volumen))

    def _obtener_sonido(self, clave: str) -> Optional[pygame.mixer.Sound]:
        if clave not in self._config_efectos:
            return None
        if clave not in self._efectos:
            ruta = self._config_efectos[clave].get("ruta")
            if not ruta:
                return None
            try:
                self._efectos[clave] = pygame.mixer.Sound(str(ruta))
            except pygame.error as error:
                print(f"Error al cargar efecto {ruta}: {error}")
                return None
        return self._efectos.get(clave)

    def _obtener_canal(self, clave: str, canal_forzado: int | None = None) -> Optional[pygame.mixer.Channel]:
        if clave in self._canales_reservados and self._canales_reservados[clave] is not None:
            return self._canales_reservados[clave]
        canal_config = self._config_efectos.get(clave, {}).get("canal")
        canal_objetivo = canal_forzado if canal_forzado is not None else canal_config
        if canal_objetivo is not None:
            try:
                canal = pygame.mixer.Channel(int(canal_objetivo))
                self._canales_reservados[clave] = canal
                return canal
            except pygame.error:
                pass
        return pygame.mixer.find_channel()

    def _aplicar_volumen(self, clave: str, volumen: float | None) -> float:
        base_config = self._config_efectos.get(clave, {}).get("volumen") if clave in self._config_efectos else 1.0
        if isinstance(base_config, (int, float)):
            base = float(base_config)
        else:
            base = 1.0
        if volumen is not None:
            base = max(0.0, min(1.0, volumen))
        volumen_final = base * self.volumen_efectos
        return max(0.0, min(1.0, volumen_final))

    def reproducir_efecto(
        self,
        clave: str,
        loops: int = 0,
        volumen: float | None = None,
        reiniciar: bool = False,
        ruta: str | None = None,
        canal: int | None = None,
    ) -> Optional[pygame.mixer.Channel]:
        if clave not in self._config_efectos:
            if ruta is None:
                return None
            self.registrar_efecto(clave, ruta, canal=canal, volumen=volumen if volumen is not None else 1.0)
        elif ruta is not None:
            if self._config_efectos[clave].get("ruta") != ruta:
                self.actualizar_ruta_efecto(clave, ruta)
        sonido = self._obtener_sonido(clave)
        if sonido is None:
            return None
        canal_audio = self._obtener_canal(clave, canal)
        if canal_audio is None:
            return None
        if not reiniciar and canal_audio.get_busy():
            self._canales_activos[clave] = canal_audio
            return canal_audio
        volumen_final = self._aplicar_volumen(clave, volumen)
        canal_audio.set_volume(volumen_final)
        canal_audio.play(sonido, loops=loops)
        self._canales_activos[clave] = canal_audio
        return canal_audio

    def detener_efecto(self, clave: str) -> None:
        canal = self._canales_activos.get(clave) or self._canales_reservados.get(clave)
        if canal and canal.get_busy():
            canal.stop()
        self._canales_activos.pop(clave, None)

    def esta_reproduciendo(self, clave: str) -> bool:
        canal = self._canales_activos.get(clave) or self._canales_reservados.get(clave)
        return bool(canal and canal.get_busy())

    def reproducir_efecto_puntual(self, ruta: str, volumen: float | None = None) -> Optional[pygame.mixer.Channel]:
        if ruta not in self._efectos_puntuales:
            try:
                self._efectos_puntuales[ruta] = pygame.mixer.Sound(ruta)
            except pygame.error as error:
                print(f"Error al cargar efecto puntual {ruta}: {error}")
                return None
        canal = pygame.mixer.find_channel()
        if canal is None:
            return None
        volumen_final = max(0.0, min(1.0, (volumen if volumen is not None else 1.0) * self.volumen_efectos))
        canal.set_volume(volumen_final)
        canal.play(self._efectos_puntuales[ruta])
        return canal

    def limpiar(self) -> None:
        try:
            for clave in list(self._canales_activos.keys()):
                self.detener_efecto(clave)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except pygame.error as error:
            print(f"Error al limpiar mixer: {error}")
