"""
forecast_views.py
Funciones de visualización runtime para pronósticos municipales.

Este módulo contiene únicamente funciones de renderizado:
- plot_forecast_ranked(): Grafica pronósticos ordenados con intervalos
"""

# ============================
# IMPORTACIONES
# ============================
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


# ============================
# DEF plot_forecast_ranked()
# ============================
def plot_forecast_ranked(
    forecast_df: pd.DataFrame,
    model_display_name: str,
    figsize: tuple[int, int] = (8, 3.5),
) -> tuple[plt.Figure, plt.Axes]:
    """
    Grafica el pronóstico municipal 2027 ordenando municipios por valor predicho.
    """
    required_cols = {"y_pred", "pi_lower", "pi_upper"}
    missing = required_cols - set(forecast_df.columns)

    if missing:
        raise ValueError(
            f"forecast_df no contiene las columnas requeridas: {sorted(missing)}"
        )

    if forecast_df.empty:
        raise ValueError("forecast_df está vacío; no hay datos para graficar.")

    df = forecast_df.copy().sort_values("y_pred").reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(
        df["rank"],
        df["y_pred"],
        linewidth=1.8,
        label="Estimación puntual",
    )

    ax.fill_between(
        df["rank"],
        df["pi_lower"],
        df["pi_upper"],
        alpha=0.25,
        label="Intervalo de predicción aprox.",
    )

    ax.set_title(f"Pronóstico municipal 2027 - {model_display_name}")
    ax.set_xlabel("Municipios ordenados por predicción")
    ax.set_ylabel("Proporción de participación esperada")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    return fig, ax