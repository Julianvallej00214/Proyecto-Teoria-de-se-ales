"""Funciones de carga, caracterización, segmentación, ruido y análisis frecuencial."""
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

import config


# ---------------------------------------------------------------- carga
def cargar_audio(ruta):
    """Carga un audio y devuelve (x, fs) con x en float [-1, 1] y monocanal.

    .wav -> scipy.io.wavfile. Otros formatos (mp3, flac) -> soundfile.
    """
    ruta = Path(ruta)
    if ruta.suffix.lower() == ".wav":
        fs, x = wavfile.read(ruta)
        if np.issubdtype(x.dtype, np.integer):
            x = x.astype(np.float64) / np.iinfo(x.dtype).max
        else:
            x = x.astype(np.float64)
    else:
        import soundfile as sf  # requiere libsndfile >= 1.1 para mp3
        x, fs = sf.read(ruta, dtype="float64")
    if x.ndim > 1:          # estéreo -> mono (promedio de canales)
        x = x.mean(axis=1)
    return x, int(fs)


def listar_audios(carpeta):
    exts = {".wav", ".mp3", ".flac", ".ogg"}
    return sorted(p for p in Path(carpeta).glob("*") if p.suffix.lower() in exts)


# ------------------------------------------------- caracterización básica
def caracterizar(x, fs):
    """Parámetros básicos de la señal en el dominio del tiempo."""
    x = np.asarray(x)
    if x.size == 0:
        raise ValueError("La señal está vacía; no se puede caracterizar.")
    if fs <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")
    return {
        "fs_Hz": fs,
        "Ts_s": 1 / fs,
        "N_muestras": len(x),
        "duracion_s": len(x) / fs,
        "minimo": float(x.min()),
        "maximo": float(x.max()),
        "media": float(x.mean()),
        "rms": float(np.sqrt(np.mean(x ** 2))),
    }


def normalizar(x):
    """Quita la media (componente DC) y normaliza al pico a 1."""
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        raise ValueError("La señal está vacía; no se puede normalizar.")
    x = x - x.mean()
    pico = np.max(np.abs(x))
    if pico == 0:
        return x
    return x / pico


# ---------------------------------------------------------- segmentación
def filtro_pasabanda(x, fs, banda=config.BANDA_AVE_HZ, orden=4):
    """Pasa-banda Butterworth para limitar la señal a la banda del canto."""
    nyq = fs / 2
    hi = min(banda[1], 0.95 * nyq)
    sos = signal.butter(orden, [banda[0] / nyq, hi / nyq], btype="band", output="sos")
    return signal.sosfiltfilt(sos, x)


def envolvente_energia(x, fs, ventana_s=config.VENTANA_ENERGIA_S):
    """Energía a corto plazo: media móvil de x^2, raíz cuadrada (RMS local)."""
    n = max(1, int(ventana_s * fs))
    return np.sqrt(np.convolve(x ** 2, np.ones(n) / n, mode="same"))


def segmentar(x, fs):
    """Detecta eventos de canto por umbral sobre la envolvente de energía.

    Devuelve (lista de (inicio_s, fin_s), envolvente, umbral).
    Criterio (ver docs/criterio_segmentacion.md):
      1. pasa-banda 1-10 kHz; 2. envolvente RMS (25 ms);
      3. umbral = UMBRAL_REL * max(envolvente); 4. se unen eventos separados
      por < 20 ms; 5. se descartan eventos < 40 ms.
    """
    xf = filtro_pasabanda(x, fs)
    env = envolvente_energia(xf, fs)
    umbral = config.UMBRAL_REL * env.max()
    activo = env > umbral
    # índices de cambio
    d = np.diff(activo.astype(int))
    ini = list(np.where(d == 1)[0] + 1)
    fin = list(np.where(d == -1)[0] + 1)
    if activo[0]:
        ini = [0] + ini
    if activo[-1]:
        fin = fin + [len(x)]
    ev = [[i / fs, f / fs] for i, f in zip(ini, fin)]
    # unir eventos cercanos
    unidos = []
    for e in ev:
        if unidos and e[0] - unidos[-1][1] < config.UNION_HUECO_S:
            unidos[-1][1] = e[1]
        else:
            unidos.append(e)
    unidos = [tuple(e) for e in unidos if e[1] - e[0] >= config.DURACION_MIN_S]
    return unidos, env, umbral


# ------------------------------------------------------------------ ruido
def agregar_ruido_gaussiano(x, snr_db, rng):
    """Suma ruido blanco gaussiano para lograr una SNR dada (dB).

    SNR = 10 log10(P_senal / P_ruido)  ->  P_ruido = P_senal / 10^(SNR/10)
    """
    p_senal = np.mean(x ** 2)
    p_ruido = p_senal / (10 ** (snr_db / 10))
    return x + rng.normal(0, np.sqrt(p_ruido), len(x))


def snr_medida(x_limpia, x_ruidosa):
    r = x_ruidosa - x_limpia
    return 10 * np.log10(np.mean(x_limpia ** 2) / np.mean(r ** 2))


# -------------------------------------------------- análisis frecuencial
def espectro_fft(x, fs):
    """Magnitud de la FFT (lado positivo) con ventana de Hann.

    Eje de frecuencias: f_k = k * fs / N. Magnitud normalizada por la suma de
    la ventana para que una sinusoide de amplitud A dé un pico ~A.
    """
    w = np.hanning(len(x))
    X = np.fft.rfft(x * w)
    f = np.fft.rfftfreq(len(x), 1 / fs)
    mag = 2 * np.abs(X) / np.sum(w)
    return f, mag


def espectrograma(x, fs, nperseg=1024, solape=0.75):
    """STFT en dB. Resolución en frecuencia = fs/nperseg; en tiempo = nperseg/fs."""
    noverlap = int(nperseg * solape)
    f, t, S = signal.spectrogram(x, fs, window="hann", nperseg=nperseg,
                                 noverlap=noverlap, mode="magnitude")
    return f, t, 20 * np.log10(S + 1e-10)


def caracteristicas_espectrales(f, mag):
    """Frecuencia dominante, centroide y ancho de banda espectral (Hz)."""
    banda = (f >= config.BANDA_AVE_HZ[0]) & (f <= config.BANDA_AVE_HZ[1])
    fb, mb = f[banda], mag[banda]
    p = mb ** 2
    centroide = np.sum(fb * p) / np.sum(p)
    ancho = np.sqrt(np.sum(((fb - centroide) ** 2) * p) / np.sum(p))
    return {"f_dominante_Hz": float(fb[np.argmax(mb)]),
            "centroide_Hz": float(centroide),
            "ancho_banda_Hz": float(ancho)}
