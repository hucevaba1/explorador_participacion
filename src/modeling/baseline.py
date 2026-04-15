"""
baseline.py
ARCHIVO CON LOS PRONÓSTICOS DE REFERENCIA (BASELINE) PARA COMPARAR LOS MODELOS (REGRESIÓN LINEA, RIDGE Y RANDOM FOREST) EN EL ANÁLISIS ELECTORAL
"""
# =====================================================
# IMPORTACIONES
# =====================================================
from __future__ import annotations
import pandas as pd

# =====================================================
# DEF baseline_naive_last_value(): GENERA UN PRONÓSTICO DE REFERENCIA (BASELINE) QUE ASIGNA EL ÚLTIMO VALOR OBSERVADO COMO PRONÓSTICO PARA EL SIGUIENTE PERÍODO.
# =====================================================
def baseline_naive_last_value(
    df: pd.DataFrame,
    target_col: str = "target_sv_ratio_next",
    lag_col: str = "lag_sv_ratio_1",
) -> pd.DataFrame:
    """
    Crea el baseline naive: El siguiente valor predicho es igual al último observado.
        Recibe: 
            - df: DataFrame con los datos.
            - target_col: nombre de la columna con el valor objetivo (Yt+1).
            - lag_col: nombre de la columna con el último valor observado (Yt).
        Devuelve:
            - DataFrame con columnas 'y_true' (valor objetivo) y 'y_pred' (valor predicho por el baseline).
    """
    out = df.copy()
    out["y_true"] = out[target_col]
    out["y_pred"] = out[lag_col]
    return out

#=====================================================
# DEF baseline_historical_mean(): GENERA UN PRONÓSTICO DE REFERENCIA (BASELINE)
# ASIGNA EL PROMEDIO HISTÓRICO MUNICIPAL HASTA EL PERÍODO ACTUAL COMO PRONÓSTICO PARA EL SIGUIENTE PERÍODO.
#=====================================================
def baseline_historical_mean(
    df: pd.DataFrame,
    target_col: str = "target_sv_ratio_next",
) -> pd.DataFrame:
    """
    Crea el baseline de promedio histórico municipal hasta t
        Recibe:
            - df: DataFrame con los datos.
            - target_col: nombre de la columna con el valor objetivo (Yt+1).
        Devuelve:
            - DataFrame con columnas 'y_true' (valor objetivo) y 'y_pred' (valor predicho por el baseline).
    """
    out = df.copy().sort_values(["CVEGEO", "year"]).reset_index(drop=True)

    expanding_mean = (
        out.groupby("CVEGEO", observed=True)["sv_ratio"]
        .transform(lambda s: s.expanding().mean())
    )

    out["y_true"] = out[target_col] 
    out["y_pred"] = expanding_mean #El promedio histórico disponible en t debe excluir el target futuro, así que el valor en t sirve como predicción de t+1. 

    return out