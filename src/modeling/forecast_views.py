"""
forecast_views.py
ARCHIVO CON FUNCIONES PARA CONTRUIR PLOTS CON PRONOSTICOS MUNICIPALES 2027 Y SUS INTERVALOS DE PREDICCIÓN APROXIMADOS USANDO ERROR FUERA DE MUESTRA
La función add_prediction_interval_from_oos_error() construye un intervalo de predicción aproximado usando la desviación estándar del error fuera de 
muestra de un modelo específico. 
La función plot_forecast_ranked() grafica el pronóstico municipal 2027 ordenando municipios por valor predicho, mostrando la estimación puntual y un intervalo
de predicción aproximado para cada municipio.
"""
#============================
# IMPORTACIONES
#============================
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

#============================
# DEF add_prediction_interval_from_oos_error(): CONSTRUYE INTERVALO DE PREDICCIÓN APROXIMADO USANDO ERROR FUERA DE MUESTRA
#============================
def add_prediction_interval_from_oos_error(
    forecast_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
    model_name: str,
    z_value: float = 1.96,
) -> pd.DataFrame:
    """
    Construye un intervalo de predicción aproximado usando la desviación estándar del error fuera de muestra de un modelo específico.
    El intervalo se calcula como: y_pred ± z_value * error_std, donde error_std es la desviación estándar de los errores fuera de muestra para el modelo dado.
        Recibe:
        - forecast_df: DataFrame con al menos la columna 'y_pred' para el pronóstico municipal 2027.
        - predictions_df: DataFrame con columnas 'model' y 'error' que contiene los errores fuera de muestra de diferentes modelos.
        - model_name: Nombre del modelo para el cual se desea calcular el intervalo de predicción.
        - z_value: Valor z para el nivel de confianza deseado (por defecto 1.96 para un intervalo del 95%).
        Devuelve:
        - DataFrame con columnas adicionales 'pi_lower' y 'pi_upper' que representan los límites inferior y superior del intervalo de predicción, respectivamente. 
            Los límites se ajustan para asegurar que estén dentro del rango [0, 1].
    """
    out = forecast_df.copy()

    if "y_pred" not in out.columns:
        raise ValueError("forecast_df debe contener la columna 'y_pred'.")

    required_pred_cols = {"model", "error"}
    missing_pred_cols = required_pred_cols - set(predictions_df.columns)
    if missing_pred_cols:
        raise ValueError(
            "predictions_df no contiene las columnas requeridas: "
            f"{sorted(missing_pred_cols)}"
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

#============================
# DEF plot_forecast_ranked(): GRAFICA PRONÓSTICO MUNICIPAL 2027 ORDENANDO MUNICIPIOS POR VALOR PREDICHO
#============================
def plot_forecast_ranked(
    forecast_df: pd.DataFrame,
    model_display_name: str,
    figsize: tuple[int, int] = (8, 3.5),
)-> tuple[plt.Figure, plt.Axes]:
    """
    Grafica el pronóstico municipal 2027 ordenando municipios por valor predicho.
        Recibe:
            - forecast_df: DataFrame con columnas 'y_pred', 'pi_lower' y 'pi_upper'.
            - model_display_name: Nombre del modelo para el cual se desea graficar el pronóstico.
            - figsize: Tamaño de la figura (por defecto (10, 4)).
        Devuelve:
            - fig, ax: Objeto de figura y eje de Matplotlib con la gráfica del pronóstico municipal 2027. La gráfica muestra la estimación puntual y un intervalo de predicción aproximado para cada municipio.
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
