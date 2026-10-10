"""Configuración central del proyecto.

Modifica CLASES para cambiar las especies analizadas. El nombre de cada clase
debe coincidir con el nombre de la subcarpeta en data/raw/ (o data/synthetic/).
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_SINT = RAIZ / "data" / "synthetic"
DIR_RESULTADOS = RAIZ / "results"

# Especies (clases) del proyecto: nombre de carpeta -> consulta a Xeno-canto
CLASES = {
    "Zonotrichia_capensis": "Zonotrichia capensis",  # Copetón / Chingolo
    "Troglodytes_aedon": "Troglodytes aedon",        # Cucarachero común
}

# Parámetros de segmentación (ver docs/criterio_segmentacion.md)
VENTANA_ENERGIA_S = 0.025   # ventana para energía a corto plazo (25 ms)
UMBRAL_REL = 0.10           # fracción del máximo de energía (envolvente)
DURACION_MIN_S = 0.04       # descarta eventos más cortos que 40 ms
UNION_HUECO_S = 0.02        # une eventos separados por menos de 20 ms
BANDA_AVE_HZ = (1000, 10000)  # banda donde se espera el canto

# Parámetros de ruido
SNR_DB_LISTA = [20, 10, 0]
SEMILLA = 42
