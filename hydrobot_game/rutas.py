import sys
from pathlib import Path


def _directorio_raiz() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def ruta_relativa(*segmentos: str) -> str:
    return str(_directorio_raiz().joinpath(*segmentos))


def ruta_recurso(*segmentos: str) -> str:
    return ruta_relativa("recursos", *segmentos)
