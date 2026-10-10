"""Descarga grabaciones de Xeno-canto para las clases definidas en config.py.

Uso:
    python src/descargar_xenocanto.py --n 5
    python src/descargar_xenocanto.py --n 5 --pais Colombia

Xeno-canto (https://xeno-canto.org) publica las grabaciones bajo licencias
Creative Commons; cada archivo guarda su metadatos (autor, licencia, id) en
data/raw/<clase>/metadatos.csv para poder citarlos.

NOTA: la API v2 puede requerir una clave (ver https://xeno-canto.org/explore/api).
Si la API falla, descarga manualmente 3-5 archivos por especie desde la web y
colócalos en data/raw/<clase>/.
"""
import argparse
import csv
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CLASES, DIR_RAW  # noqa: E402

API = "https://xeno-canto.org/api/2/recordings"


def descargar(clase, consulta, n, pais, calidad):
    destino = DIR_RAW / clase
    destino.mkdir(parents=True, exist_ok=True)
    q = f'{consulta} q:{calidad}'
    if pais:
        q += f" cnt:{pais}"
    r = requests.get(API, params={"query": q}, timeout=30)
    r.raise_for_status()
    grabaciones = r.json().get("recordings", [])[:n]
    if not grabaciones:
        print(f"[{clase}] sin resultados para: {q}")
        return
    filas = []
    for g in grabaciones:
        url = g["file"]
        nombre = f"XC{g['id']}.mp3"
        ruta = destino / nombre
        if not ruta.exists():
            print(f"[{clase}] descargando {nombre}")
            with requests.get(url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                with open(ruta, "wb") as f:
                    for trozo in resp.iter_content(1 << 16):
                        f.write(trozo)
        filas.append({
            "archivo": nombre, "id": g["id"], "especie": f"{g['gen']} {g['sp']}",
            "autor": g["rec"], "pais": g["cnt"], "licencia": g["lic"],
            "tipo": g["type"], "url": g["url"],
        })
    with open(destino / "metadatos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=5, help="grabaciones por especie")
    p.add_argument("--pais", default="", help="filtro de país (opcional)")
    p.add_argument("--calidad", default="A", help="calidad Xeno-canto (A-E)")
    a = p.parse_args()
    for clase, consulta in CLASES.items():
        descargar(clase, consulta, a.n, a.pais, a.calidad)
