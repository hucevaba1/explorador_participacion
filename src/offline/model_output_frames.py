"""
model_output_frames.py
Funciones para estandarizar outputs de predicción y generar
dataframes listos para evaluación, diagnóstico offline y materialización.
"""

# ==================================
# IMPORTACIONES
# ==================================
from __future__ import annotations

import pandas as pd

from src.base.validator import validate_required_columns


# ==================================
# DEF build_prediction_frame()
# ==================================
def build_prediction_frame(
    pred_df: pd.DataFrame,
    model_name: str,
    target_col: str,
    test_year: int,
) -> pd.DataFrame:
    """
    Estandariza el output de predicción para diagnóstico offline.

    Recibe:
        - pred_df: DataFrame con al menos columnas "y_pred" y target_col (real).
        - model_name: Nombre del modelo.
        - target_col: Nombre de la columna con los valores reales.
        - test_year: Año de prueba.

    Devuelve:
        - DataFrame con columnas:
          "model", "test_year", "CVEGEO", "municipio", "state_code",
          "year", "y_true", "y_pred", "error", "abs_error"
    """
    work = pred_df.copy()

    required_cols = ["CVEGEO", "municipio", "state_code", "year", "y_pred"]
    validate_required_columns(
        work,
        required_cols,
        context="model_output_frames",
    )

    if "y_true" not in work.columns:
        if target_col not in work.columns:
            raise ValueError(
                f"pred_df debe contener 'y_true' o la columna target {target_col!r}."
            )
        work["y_true"] = work[target_col]

    work["error"] = work["y_pred"] - work["y_true"]
    work["abs_error"] = work["error"].abs()

    cols = [
        "CVEGEO",
        "municipio",
        "state_code",
        "year",
        "y_true",
        "y_pred",
        "error",
        "abs_error",
    ]

    out = work[cols].copy()
    out["model"] = model_name
    out["test_year"] = test_year

    ordered_cols = [
        "model",
        "test_year",
        "CVEGEO",
        "municipio",
        "state_code",
        "year",
        "y_true",
        "y_pred",
        "error",
        "abs_error",
    ]

    return out[ordered_cols]