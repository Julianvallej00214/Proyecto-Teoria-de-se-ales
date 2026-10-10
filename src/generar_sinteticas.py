"""Genera señales SIMULADAS tipo canto de ave, solo para probar el pipeline.

IMPORTANTE: no son grabaciones reales. Son modelos sencillos construidos por
nosotros (barridos de frecuencia y trinos) con fs = 22050 Hz, para poder
ejecutar el código sin conexión. Cuando se descarguen grabaciones reales
(ver descargar_xenocanto.py), el pipeline las usa automáticamente.

Clase A (Zonotrichia_capensis_sim): notas largas con barrido descendente
    suave (~4.5 -> 3 kHz), pocas notas y pausas largas.
Clase B (Troglodytes_aedon_sim): trino rápido de notas cortas con barrido
    ascendente (~3 -> 6 kHz), muchas notas y pausas cortas.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DIR_SINT, SEMILLA  # noqa: E402

FS = 22050


def nota(f0, f1, dur, fs=FS, armonico=0.3):
    """Nota con barrido lineal de f0 a f1 (Hz), envolvente suave y 2º armónico."""
    t = np.arange(int(dur * fs)) / fs
    k = (f1 - f0) / dur
    fase = 2 * np.pi * (f0 * t + 0.5 * k * t ** 2)
    x = np.sin(fase) + armonico * np.sin(2 * fase)
    return x * np.hanning(len(t))


def canto(rng, notas, f0, f1, dur_nota, pausa, total_s, fs=FS):
    x = np.zeros(int(total_s * fs))
    pos = int(0.3 * fs)
    for _ in range(notas):
        d = dur_nota * rng.uniform(0.85, 1.15)
        df = rng.uniform(-150, 150)
        n = nota(f0 + df, f1 + df, d)
        if pos + len(n) >= len(x):
            break
        x[pos:pos + len(n)] += n * rng.uniform(0.7, 1.0)
        pos += len(n) + int(pausa * rng.uniform(0.8, 1.2) * fs)
    x += 0.003 * rng.standard_normal(len(x))  # ruido de fondo leve
    return x / np.max(np.abs(x)) * 0.8


def main(n_por_clase=3):
    if n_por_clase < 1:
        raise ValueError("n_por_clase debe ser al menos 1.")
    rng = np.random.default_rng(SEMILLA)
    for clase, args in {
        "Zonotrichia_capensis_sim": dict(notas=4, f0=4500, f1=3000, dur_nota=0.45, pausa=0.25),
        "Troglodytes_aedon_sim": dict(notas=14, f0=3000, f1=6000, dur_nota=0.08, pausa=0.04),
    }.items():
        carpeta = DIR_SINT / clase
        carpeta.mkdir(parents=True, exist_ok=True)
        for i in range(n_por_clase):
            x = canto(rng, total_s=5.0, **args)
            wavfile.write(carpeta / f"{clase}_{i + 1:02d}.wav", FS, (x * 32767).astype(np.int16))
    print("Señales simuladas generadas en", DIR_SINT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera audios sintéticos de prueba para dos clases de aves.")
    parser.add_argument(
        "--n-por-clase", type=int, default=3,
        help="cantidad de archivos WAV que se generan por clase (por defecto: 3)",
    )
    args = parser.parse_args()
    main(args.n_por_clase)
