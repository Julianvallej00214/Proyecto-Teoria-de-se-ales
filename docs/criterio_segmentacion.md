# Criterio de segmentación

Objetivo: aislar los **eventos de canto** (notas) del silencio y del ruido de fondo, para poder comparar segmentos equivalentes entre especies.

## Procedimiento (`senales.segmentar`)

1. **Pasa-banda Butterworth (orden 4, 1–10 kHz, `sosfiltfilt`)**: elimina ruido de baja frecuencia (viento, motores, < 1 kHz) y limita la señal a la banda donde cantan las especies elegidas.
2. **Envolvente de energía**: raíz de la media móvil de x² en ventanas de 25 ms (RMS local).
3. **Umbral** = 10 % del máximo de la envolvente. Es relativo, para que funcione con grabaciones de distinto nivel de grabación.
4. **Unión de huecos**: eventos separados por menos de 20 ms se consideran el mismo evento.
5. **Duración mínima**: se descartan eventos de menos de 40 ms (clics, ruido impulsivo).

## Parámetros (en `src/config.py`)

| Parámetro | Valor | Justificación |
|---|---|---|
| `VENTANA_ENERGIA_S` | 25 ms | Más corta que las notas más cortas esperadas (~80 ms) |
| `UMBRAL_REL` | 0.10 | Compromiso: bajo para no cortar notas débiles, alto para ignorar el ruido |
| `UNION_HUECO_S` | 20 ms | Menor que la pausa entre notas de un trino (~40 ms) para no fusionarlas |
| `DURACION_MIN_S` | 40 ms | Evita falsos positivos por ruido impulsivo |

## Limitaciones conocidas

- Con ruido fuerte (SNR bajo) o grabaciones con varias aves cantando, el umbral relativo puede fallar; se revisará en la entrega final (umbral adaptativo, estimación del ruido de fondo).
- Los parámetros se ajustaron con señales **simuladas**; hay que recalibrarlos con las grabaciones reales.
- El primer valor de `UNION_HUECO_S` fue 100 ms y fundía todo el trino de la clase B en un solo evento; se bajó a 20 ms tras revisar la gráfica de segmentación.
