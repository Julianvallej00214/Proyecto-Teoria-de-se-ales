"""Análisis inicial de cantos de aves: genera gráficas y tablas en results/.

Uso:
    python src/analisis_inicial.py            # usa data/raw si hay audios, si no data/synthetic
    python src/analisis_inicial.py --fuente synthetic
    python src/analisis_inicial.py --fuente raw
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
import senales as sg


def descubrir_clases(fuente):
    """Devuelve {clase: [rutas]} según la fuente de datos elegida."""
    base = {"raw": config.DIR_RAW, "synthetic": config.DIR_SINT}
    orden = [fuente] if fuente != "auto" else ["raw", "synthetic"]
    for f in orden:
        clases = {}
        if base[f].exists():
            for sub in sorted(p for p in base[f].iterdir() if p.is_dir()):
                audios = sg.listar_audios(sub)
                if audios:
                    clases[sub.name] = audios
        if len(clases) >= 2:
            return f, clases
    raise SystemExit("No hay audios de al menos 2 clases. Ejecuta "
                     "src/descargar_xenocanto.py o src/generar_sinteticas.py")


def graficar_forma_onda(x, fs, nombre, ruta):
    t = np.arange(len(x)) / fs
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(t, x, lw=0.5)
    ax.set(xlabel="Tiempo (s)", ylabel="Amplitud (normalizada)",
           title=f"Forma de onda - {nombre}")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(ruta, dpi=150); plt.close(fig)


def graficar_segmentacion(x, fs, eventos, env, umbral, nombre, ruta):
    t = np.arange(len(x)) / fs
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(t, x, lw=0.4, color="0.6", label="señal")
    ax.plot(t, env * np.max(np.abs(x)) / env.max(), color="C1", lw=1,
            label="envolvente RMS (escalada)")
    ax.axhline(umbral * np.max(np.abs(x)) / env.max(), color="C3", ls="--",
               label=f"umbral ({config.UMBRAL_REL:.0%} del máx.)")
    for i, (a, b) in enumerate(eventos):
        ax.axvspan(a, b, color="C2", alpha=0.25, label="evento" if i == 0 else None)
    ax.set(xlabel="Tiempo (s)", ylabel="Amplitud",
           title=f"Segmentación por energía - {nombre} ({len(eventos)} eventos)")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout(); fig.savefig(ruta, dpi=150); plt.close(fig)


def graficar_espectro(x, fs, nombre, ruta):
    f, mag = sg.espectro_fft(x, fs)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(f / 1000, 20 * np.log10(mag + 1e-10), lw=0.6)
    ax.set(xlabel="Frecuencia (kHz)", ylabel="Magnitud (dB)", xlim=(0, 12),
           title=f"Espectro FFT (ventana de Hann) - {nombre}")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(ruta, dpi=150); plt.close(fig)


def graficar_espectrograma(x, fs, nombre, ruta):
    f, t, S = sg.espectrograma(x, fs)
    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.pcolormesh(t, f / 1000, S, shading="auto", vmin=S.max() - 70, cmap="magma")
    ax.set(xlabel="Tiempo (s)", ylabel="Frecuencia (kHz)", ylim=(0, 10),
           title=f"Espectrograma (STFT, 1024 muestras, 75 % solape)\n{nombre}", )
    fig.colorbar(im, ax=ax, label="Magnitud (dB)")
    fig.tight_layout(); fig.savefig(ruta, dpi=150); plt.close(fig)


def graficar_ruido(x, fs, nombre, ruta, rng):
    """Señal original vs. con ruido gaussiano a varias SNR (tiempo y espectrograma)."""
    versiones = [("original", x)]
    for snr in config.SNR_DB_LISTA:
        versiones.append((f"SNR = {snr} dB", sg.agregar_ruido_gaussiano(x, snr, rng)))
    fig, axs = plt.subplots(2, len(versiones), figsize=(3.6 * len(versiones), 6),
                            sharey="row")
    for j, (et, xv) in enumerate(versiones):
        t = np.arange(len(xv)) / fs
        axs[0, j].plot(t, xv, lw=0.4)
        axs[0, j].set(title=et, xlabel="Tiempo (s)")
        f, tt, S = sg.espectrograma(xv, fs)
        axs[1, j].pcolormesh(tt, f / 1000, S, shading="auto", vmin=S.max() - 70, cmap="magma")
        axs[1, j].set(xlabel="Tiempo (s)", ylim=(0, 10))
    axs[0, 0].set_ylabel("Amplitud"); axs[1, 0].set_ylabel("Frecuencia (kHz)")
    fig.suptitle(f"Efecto del ruido blanco gaussiano - {nombre}")
    fig.tight_layout(); fig.savefig(ruta, dpi=150); plt.close(fig)


def graficar_comparacion(espectros, ruta):
    fig, ax = plt.subplots(figsize=(10, 4))
    for clase, (f, mag) in espectros.items():
        ax.plot(f / 1000, mag / mag.max(), lw=0.8, label=clase)
    ax.set(xlabel="Frecuencia (kHz)", ylabel="Magnitud normalizada", xlim=(0, 10),
           title="Comparación del espectro entre clases (promedio de eventos)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(ruta, dpi=150); plt.close(fig)


def main(fuente):
    rng = np.random.default_rng(config.SEMILLA)
    fuente, clases = descubrir_clases(fuente)
    print(f"Fuente de datos: {fuente}  |  clases: {list(clases)}")
    out = config.DIR_RESULTADOS
    out.mkdir(exist_ok=True)

    filas_car, filas_feat, espectros_clase = [], [], {}
    for clase, rutas in clases.items():
        acum_mag, nacum = None, 0
        for k, ruta in enumerate(rutas):
            x, fs = sg.cargar_audio(ruta)
            car = sg.caracterizar(x, fs)
            x = sg.normalizar(x)
            eventos, env, umbral = sg.segmentar(x, fs)
            etiqueta = f"{clase} / {ruta.name}"
            filas_car.append({"clase": clase, "archivo": ruta.name, **car,
                              "n_eventos": len(eventos)})

            # Features por archivo
            dur_ev = [b - a for a, b in eventos]
            pausas = [eventos[i + 1][0] - eventos[i][1] for i in range(len(eventos) - 1)]
            mags = []
            for a, b in eventos:
                seg = x[int(a * fs):int(b * fs)]
                seg = np.pad(seg, (0, max(0, 4096 - len(seg))))[:max(len(seg), 4096)]
                f, m = sg.espectro_fft(seg, fs)
                mags.append(np.interp(np.linspace(0, 12000, 2000), f, m))
            if mags:
                m_prom = np.mean(mags, axis=0)
                fgrid = np.linspace(0, 12000, 2000)
                feat = sg.caracteristicas_espectrales(fgrid, m_prom)
                acum_mag = m_prom if acum_mag is None else acum_mag + m_prom
                nacum += 1
            else:
                feat = {}
            filas_feat.append({
                "clase": clase, "archivo": ruta.name, "n_eventos": len(eventos),
                "dur_evento_media_s": float(np.mean(dur_ev)) if dur_ev else np.nan,
                "pausa_media_s": float(np.mean(pausas)) if pausas else np.nan,
                "eventos_por_s": len(eventos) / car["duracion_s"], **feat})

            # Gráficas detalladas solo para el primer archivo de cada clase
            if k == 0:
                graficar_forma_onda(x, fs, etiqueta, out / f"01_onda_{clase}.png")
                graficar_segmentacion(x, fs, eventos, env, umbral, etiqueta,
                                      out / f"02_segmentacion_{clase}.png")
                graficar_espectro(x, fs, etiqueta, out / f"03_espectro_{clase}.png")
                graficar_espectrograma(x, fs, etiqueta, out / f"04_espectrograma_{clase}.png")
                graficar_ruido(x, fs, etiqueta, out / f"05_ruido_{clase}.png", rng)
                x_n = sg.agregar_ruido_gaussiano(x, 10, rng)
                print(f"  [{clase}] SNR objetivo 10 dB -> medida {sg.snr_medida(x, x_n):.2f} dB")
        if nacum:
            espectros_clase[clase] = (np.linspace(0, 12000, 2000), acum_mag / nacum)

    graficar_comparacion(espectros_clase, out / "06_comparacion_espectros.png")
    pd.DataFrame(filas_car).to_csv(out / "caracterizacion_basica.csv", index=False)
    feats = pd.DataFrame(filas_feat)
    feats.to_csv(out / "caracteristicas_por_archivo.csv", index=False)
    resumen = feats.groupby("clase").mean(numeric_only=True).round(3)
    resumen.to_csv(out / "resumen_por_clase.csv")
    print("\nResumen por clase:\n", resumen.T.to_string())
    (out / "fuente_usada.txt").write_text(fuente + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--fuente", choices=["auto", "raw", "synthetic"], default="auto")
    main(p.parse_args().fuente)
