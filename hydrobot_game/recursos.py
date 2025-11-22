import sys
from pathlib import Path


def obtener_ruta_recurso(relativa: str) -> str:
    base = Path(__file__).resolve().parent
    base = Path(getattr(sys, "_MEIPASS", base)) if hasattr(sys, "_MEIPASS") else base
    ruta = base / relativa
    return str(ruta)
