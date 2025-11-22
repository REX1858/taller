import pygame
import os
from typing import Optional

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class AnimadorGif:
    def __init__(self, ruta_gif: str, velocidad_fotogramas: int = 100) -> None:
        self.ruta_gif = ruta_gif
        self.velocidad_fotogramas = velocidad_fotogramas
        self.fotogramas: list[pygame.Surface] = []
        self.indice_fotograma = 0
        self.tiempo_transcurrido = 0.0
        self.en_reproduccion = True
        self._cargar_gif()

    def _cargar_gif(self) -> None:
        try:
            if not os.path.exists(self.ruta_gif):
                self._crear_placeholder()
                return
            
            if not HAS_PIL:
                import subprocess
                subprocess.check_call(['pip', 'install', 'Pillow'])
            
            from PIL import Image as PILImage
            
            gif = PILImage.open(self.ruta_gif)
            duracion = 0
            frame_index = 0
            
            while True:
                try:
                    gif.seek(frame_index)
                    fotograma_pil = gif.convert("RGBA")
                    datos = pygame.image.fromstring(
                        fotograma_pil.tobytes(),
                        fotograma_pil.size,
                        "RGBA"
                    )
                    self.fotogramas.append(datos)
                    
                    if "duration" in gif.info:
                        duracion = gif.info["duration"]
                    
                    frame_index += 1
                except EOFError:
                    break
            
            if duracion > 0:
                self.velocidad_fotogramas = duracion
        except Exception:
            self._crear_placeholder()

    def _crear_placeholder(self) -> None:
        placeholder = pygame.Surface((50, 50))
        placeholder.fill((0, 180, 255))
        self.fotogramas = [placeholder]

    def actualizar(self, dt: float) -> None:
        if not self.en_reproduccion or not self.fotogramas:
            return
        
        self.tiempo_transcurrido += dt * 1000
        fotogramas_tiempo = self.velocidad_fotogramas / 1000.0
        
        if self.tiempo_transcurrido >= self.velocidad_fotogramas:
            self.tiempo_transcurrido = 0.0
            self.indice_fotograma = (self.indice_fotograma + 1) % len(self.fotogramas)

    def obtener_fotograma_actual(self) -> pygame.Surface:
        if not self.fotogramas:
            self._crear_placeholder()
        return self.fotogramas[self.indice_fotograma]

    def pausar(self) -> None:
        self.en_reproduccion = False

    def reanudar(self) -> None:
        self.en_reproduccion = True

    def reiniciar(self) -> None:
        self.indice_fotograma = 0
        self.tiempo_transcurrido = 0.0
        self.en_reproduccion = True

    def establecer_velocidad(self, velocidad: int) -> None:
        self.velocidad_fotogramas = max(1, velocidad)

    def obtener_estado(self) -> bool:
        return self.en_reproduccion
