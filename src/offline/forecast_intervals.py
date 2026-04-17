"""
forecast_intervals.py
Funciones offline para construir intervalos de predicción aproximados
a partir del error fuera de muestra.

Este módulo contiene:
- add_prediction_interval_from_oos_error()
"""

# ============================
# IMPORTACIONES
# ============================
from __future__ import annotations

import pandas as pd

from src.base.validator import validate_required_columns


# ============================
# DEF add_prediction_interval_from_oos_error()
# ============================
def add_prediction_interval_from_oos_error(
    forecast_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
    model_name: str,
    z_value: float = 1.96,
) -> pd.DataFrame:
    """
    Construye un intervalo de predicción aproximado usando la desviación
    estándar del error fuera de muestra de un modelo específico.
    """
    out = forecast_df.copy()

    validate_required_columns(
        out,
        ["y_pred"],
        context="forecast_intervals",
    )
    validate_required_columns(
        predictions_df,
        ["model", "error"],
        context="forecast_intervals",
    )

    model_errors = (
        predictions_df.loc[predictions_df["model"] == model_name, "error"]
        .dropna()
    )

    if model_errors.empty:
        raise ValueError(
            f"No hay errores fuera de muestra disponibles para el modelo {model_name!r}."
        )

    error_std = model_errors.std()

    if pd.isna(error_std):
        raise ValueError(
            f"No fue posible estimar la desviación estándar del error para el modelo {model_name!r}."
        )

    out["pi_lower"] = (out["y_pred"] - z_value * error_std).clip(lower=0)
    out["pi_upper"] = (out["y_pred"] + z_value * error_std).clip(upper=1)

    return out