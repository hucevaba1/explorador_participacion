"""
evaluation.py
ARCHIVO DE EVALUACIÓN DE PREDICCIONES DE MODELOS PARA EL PROYECTO ELECTORAL:
Este módulo proporciona funciones para evaluar la precisión de las predicciones utilizando:
        - Error Absoluto Medio (MAE)
        - Raíz del Error Cuadrático Medio (RMSE)
        - Tamaño de la muestra (n)
"""

#---------------------------------------
# IMPORTACIONES
#---------------------------------------
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
)
from src.base.validator import validate_required_columns

#---------------------------------------
# DEF evaluate_predictions: EVALUACIÓN DE PREDICCIONES
#---------------------------------------
def evaluate_predictions(df: pd.DataFrame) -> dict[str, float]:
    """
    Evalúa las predicciones de un modelo utilizando MAE, RMSE y tamaño de la muestra.
        Recibe: 
            - df: DataFrame con columnas 'y_true' y 'y_pred'
        Devuelve:
            - diccionario con 'mae', 'rmse' y 'n'
    """
    validate_required_columns(
        df,
        ["y_true", "y_pred"],
        context="evaluation",
    )

    work = df.dropna(subset=["y_true", "y_pred"]).copy()

    if work.empty:
        return {"mae": np.nan, "rmse": np.nan, "n": 0}

    mae = mean_absolute_error(work["y_true"], work["y_pred"])
    rmse = np.sqrt(mean_squared_error(work["y_true"], work["y_pred"]))

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "n": int(len(work)),
    }