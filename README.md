# Reconocimiento de aves mediante su canto

**Asignatura:** Teoría de Señales — Segunda entrega
**Integrantes:** Sofia Vanegas Martínez · Andrés Julián Vallejo Arango

## 1. Descripción

Se estudia el canto de aves como una **señal de audio** (variación de presión sonora muestreada) para encontrar diferencias temporales y espectrales entre especies. El objetivo final es proponer un método que relacione las características extraídas con la especie.

Especies seleccionadas (configurables en `src/config.py`):

| Clase | Especie | Nombre común |
|---|---|---|
| `Zonotrichia_capensis` | *Zonotrichia capensis* | Copetón / chingolo |
| `Troglodytes_aedon` | *Troglodytes aedon* | Cucarachero común |

## 2. Estado actual

| Parte | Estado |
|---|---|
| Carga de audio y documentación de fs, Ts, duración, N | Hecho |
| Representación temporal | Hecho |
| Caracterización básica (mín., máx., media, RMS) | Hecho |
| Segmentación por energía | Hecho (calibrada con señales simuladas) |
| Ruido gaussiano a distintas SNR | Hecho |
| FFT y espectrograma (STFT) | Hecho |
| Características por evento (duración, pausa, f. dominante, centroide) | Hecho |
| Descarga de grabaciones reales (Xeno-canto) | Script listo; **falta ejecutarlo y recalibrar** |
| Clasificador | Pendiente (entrega final) |
| Filtrado / reducción de ruido | Pendiente (según avance del curso) |

> **Aviso importante:** los resultados que se muestran abajo se obtuvieron con **señales simuladas** (`data/synthetic/`), generadas por nosotros con barridos de frecuencia, solo para validar el pipeline. **No son grabaciones reales** y no se deben interpretar como características de las especies. Al ejecutar `descargar_xenocanto.py`, el análisis usa automáticamente las grabaciones reales.

## 3. Datos y recursos

- **Grabaciones reales:** [Xeno-canto](https://xeno-canto.org), bajo licencias Creative Commons. `src/descargar_xenocanto.py` las baja y guarda autor, licencia e id en `data/raw/<clase>/metadatos.csv`. Las grabaciones **no se suben a GitHub** (ver `.gitignore`).
- **Señales simuladas:** `src/generar_sinteticas.py` (fs = 22 050 Hz, 5 s, 3 archivos por clase, semilla fija). Se incluyen en el repositorio por ser pequeñas.
  - La semilla fija (`SEMILLA = 42`) hace reproducibles las señales generadas. El número de WAV se configura con `--n-por-clase` (debe ser al menos 1); si no se indica, se generan 3 archivos por clase.
  - Clase A (`Zonotrichia_capensis_sim`): 4 notas largas (~0.45 s), barrido descendente 4.5 → 3 kHz.
  - Clase B (`Troglodytes_aedon_sim`): trino de 14 notas cortas (~0.08 s), barrido ascendente 3 → 6 kHz.

## 4. Cómo ejecutar

Python 3.10+ (probado con 3.13).

```bash
pip install -r requirements.txt

# Opción A: demostración inmediata con señales simuladas
python src/generar_sinteticas.py                 # 3 archivos por clase
python src/generar_sinteticas.py --n-por-clase 5 # 5 archivos por clase
python src/analisis_inicial.py --fuente synthetic

# Opción B: con grabaciones reales (requiere internet)
python src/descargar_xenocanto.py --n 5
python src/analisis_inicial.py --fuente raw
```

Si ejecutas `analisis_inicial.py` sin argumentos, usa `data/raw/` si hay audios de al menos 2 clases y, si no, `data/synthetic/`. Las gráficas y tablas se guardan en `results/`.

> Si la API de Xeno-canto exige clave o falla, descarga manualmente 3–5 archivos por especie y colócalos en `data/raw/<clase>/` (los nombres de carpeta deben coincidir con `config.CLASES`). Se leen `.wav`, `.mp3`, `.flac` y `.ogg`.

## 5. Conceptos de Teoría de Señales utilizados

- **Señal en tiempo continuo y su muestreo:** x[n] = x(nTs), con fs (Hz) y Ts = 1/fs (s). Se documentan fs, Ts, N y duración = N/fs.
- **Representación temporal y caracterización:** mínimo, máximo, media (componente DC), valor RMS (potencia promedio).
- **Procesamiento:** eliminación de la media, normalización al pico, filtro pasa-banda Butterworth (1–10 kHz), envolvente de energía a corto plazo.
- **Análisis frecuencial:** FFT con ventana de Hann; frecuencias f_k = k·fs/N; frecuencia dominante, centroide y ancho de banda espectral.
- **Análisis tiempo-frecuencia:** espectrograma con STFT (1024 muestras → resolución en frecuencia fs/1024 ≈ 21.5 Hz, ventana de ≈ 46 ms, 75 % de solape).
- **Ruido y SNR:** ruido blanco gaussiano aditivo, con SNR = 10·log₁₀(P_señal / P_ruido) a 20, 10 y 0 dB; se verifica la SNR medida.

## 6. Resultados actuales (señales simuladas)

Resumen por clase (`results/resumen_por_clase.csv`, promedio de 3 archivos):

| | Zonotrichia (sim.) | Troglodytes (sim.) |
|---|---|---|
| Eventos en 5 s | 4 | 14 |
| Duración media del evento | 0.356 s | 0.074 s |
| Pausa media | 0.358 s | 0.044 s |
| Frecuencia dominante | 3762 Hz | 4878 Hz |
| Centroide espectral | 4072 Hz | 5090 Hz |

**Formas de onda** (`results/01_onda_*.png`). En el tiempo se distinguen las notas como paquetes de energía separados por silencio. La clase A tiene pocas notas largas; la clase B, una ráfaga de notas cortas. Fuera del canto la amplitud es casi nula (ruido de fondo leve).

**Segmentación** (`results/02_segmentacion_*.png`). La envolvente RMS supera el umbral (10 % del máximo) solo durante las notas. Se detectan 4 y 14 eventos, igual que los generados. Criterio detallado en [`docs/criterio_segmentacion.md`](docs/criterio_segmentacion.md).

**Espectro FFT** (`results/03_espectro_*.png`). Muestra dónde se concentra la energía del canto: una banda ancha entre ~3 y ~4.5 kHz para la clase A y entre ~3 y ~6 kHz para la B, más una banda de menor nivel al doble de frecuencia (2º armónico). La FFT global no indica *cuándo* ocurre cada frecuencia.

**Espectrograma** (`results/04_espectrograma_*.png`). Lo resuelve: cada nota es una línea inclinada (barrido de frecuencia) y se ve el 2º armónico por encima. La clase A tiene líneas descendentes y espaciadas; la B, líneas ascendentes y muy seguidas. Estas diferencias de pendiente, duración y repetición son las que servirán para clasificar.

**Ruido** (`results/05_ruido_*.png`). A 20 dB el canto sigue claro. A 10 dB el piso de ruido sube en el espectrograma pero las notas se distinguen. A 0 dB el ruido tiene la misma potencia que la señal: en el tiempo las notas casi se confunden y en el espectrograma solo se aprecian las componentes más fuertes (el armónico débil se pierde). Esto anticipa que la segmentación por umbral fijo tendrá problemas con SNR bajas.

**Comparación** (`results/06_comparacion_espectros.png`). Los espectros promedio de ambas clases tienen picos en frecuencias distintas (≈ 3.8 kHz y ≈ 4.9 kHz) y solo se cruzan cerca de 4 kHz; el 2º armónico aparece en ≈ 7.5 kHz y por encima de 9 kHz. Esta separación tan limpia es **consecuencia de cómo se construyeron las señales simuladas**; con grabaciones reales se espera mucho más solape (y variación entre individuos), por lo que habrá que combinar la frecuencia con rasgos temporales (duración, pausas, ritmo).

## 7. Estructura del repositorio

```
src/
  config.py                 parámetros y clases
  senales.py                carga, segmentación, ruido, FFT, STFT
  analisis_inicial.py       genera gráficas y tablas
  descargar_xenocanto.py    descarga de grabaciones reales
  generar_sinteticas.py     señales simuladas de prueba
data/raw/                   grabaciones reales (no versionadas)
data/synthetic/             señales simuladas (muestra pequeña)
results/                    gráficas y CSV
docs/                       criterio de segmentación
notebooks/                  (reservado)
```

## 8. Pendiente para la entrega final

- Descargar y analizar grabaciones reales; recalibrar la segmentación.
- Probar varias grabaciones por especie y medir la variabilidad.
- Reducción de ruido / filtrado (cuando se vea en clase).
- Extracción de características más completas y clasificador.
- Validación con datos no vistos.

## 9. Referencias

- Stowell, D. (2022). Computational bioacoustics with deep learning: A review and roadmap. *PeerJ*, 10, e13152. https://doi.org/10.7717/peerj.13152
- Kahl, S., Wood, C. M., Eibl, M., & Klinck, H. (2021). BirdNET: A deep learning solution for avian diversity monitoring. *Ecological Informatics*, 61, 101236. https://doi.org/10.1016/j.ecoinf.2021.101236
- Pahuja, R., & Kumar, A. (2021). Sound-spectrogram based automatic bird species recognition using MLP classifier. *Applied Acoustics*, 180, 108077. https://doi.org/10.1016/j.apacoust.2021.108077
- Liu, D., Xiao, H., & Chen, K. (2025). Research progress in bird sounds recognition based on acoustic monitoring technology: A systematic review. *Applied Acoustics*, 228, 110285.
- Xeno-canto Foundation. *Xeno-canto: sharing bird sounds from around the world.* https://xeno-canto.org
