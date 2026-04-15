"""
diagnostics.py
ARCHIVO DE DIAGNÓSTICO PARA EL PROYECTO DE ANÁLISIS DE DATOS ELECTORALES:
Este módulo se encarga de construir los marcos de datos y visualizaciones necesarias para el diagnóstico de los modelos de predicción. Incluye funciones para:
- Estandarizar el output de predicción para diagnóstico, asegurando que tenga las columnas necesarias para análisis posteriores
- Generar scatter plots de predicho vs real para evaluar visualmente el desempeño del modelo
- Generar histogramas de errores para analizar la distribución de los errores de predicción
- Preparar un GeoDataFrame para mapear los errores de predicción a nivel municipal
- Construir mapas coropléticos interactivos del error municipal usando Plotly
"""

# ==================================
# IMPORTACIONES
# ==================================
from __future__ import annotations

import json

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px

from src.base.validator import validate_required_columns

# ==================================
# DEF build_prediction_frame(): ESTANDARIZA EL OUTPUT DE PREDICCIÓN PARA DIAGNÓSTICO
# ==================================  
def build_prediction_frame(
    pred_df: pd.DataFrame,
    model_name: str,
    target_col: str,
    test_year: int,
) -> pd.DataFrame:
    """
    Estandariza el output de predicción para diagnóstico. 
        Recibe:
            - pred_df: DataFrame con al menos columnas "y_pred" y target_col (real).
            - model_name: Nombre del modelo (string).
            - target_col: Nombre de la columna con los valores reales (string).
            - test_year: Año de prueba (int).
        Devuelve:
            - DataFrame con columnas estandarizadas para diagnóstico:
                "model", "test_year", "CVEGEO", "municipio", "state_code", "year", "y_true", "y_pred", "error", "abs_error"  
    """
    work = pred_df.copy()

    required_cols = ["CVEGEO", "municipio", "state_code", "year", "y_pred"]
    validate_required_columns(work, required_cols, context="diagnostics")

    if "y_true" not in work.columns:
        if target_col not in work.columns:
            raise ValueError(
                f"pred_df debe contener 'y_true' o la columna target {target_col!r}."
            )
        work["y_true"] = work[target_col]

    work["error"] = work["y_pred"] - work["y_true"]
    work["abs_error"] = work["error"].abs()

    cols = ["CVEGEO", "municipio", "state_code", "year",
            "y_true", "y_pred", "error", "abs_error",]

    out = work[cols].copy()
    out["model"] = model_name
    out["test_year"] = test_year

    ordered_cols = ["model", "test_year", "CVEGEO", "municipio", "state_code",
                    "year", "y_true", "y_pred", "error", "abs_error",]

    return out[ordered_cols]

# ==================================
# DEF plot_predicted_vs_real(): SCATTER PLOT DE PREDICHO VS REAL PARA DIAGNÓSTICO DE MODELO   
# ==================================
def plot_predicted_vs_real(
    predictions_df: pd.DataFrame,
    model_name: str,
    test_year: int | None = None,
    figsize: tuple[int, int] = (6, 6),
) -> tuple[plt.Figure, plt.Axes]:
    """
    Genera scatter plot de predicho vs real.
        Recibe:
            - predictions_df: DataFrame con las predicciones.
            - model_name: Nombre del modelo.
            - test_year: Año de prueba.
            - figsize: Tamaño de la figura.
        Devuelve: 
            - fig, ax: Figura y ejes del plot como tupla.
    """
    required_cols = ["model", "y_true", "y_pred"]
    validate_required_columns(predictions_df, required_cols, context="diagnostics")

    df = predictions_df[predictions_df["model"] == model_name].copy()

    if test_year is not None:
        validate_required_columns(df, ["test_year"], context="diagnostics")
        df = df[df["test_year"] == test_year].copy()

    if df.empty:
        raise ValueError("No hay datos para el modelo/año solicitado.")

    x = df["y_true"].to_numpy()
    y = df["y_pred"].to_numpy()

    min_val = float(min(x.min(), y.min()))
    max_val = float(max(x.max(), y.max()))

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x, y, alpha=0.35)

    ax.plot(
        [min_val, max_val],
        [min_val, max_val],
        linestyle="--",
        linewidth=1.5,
    )

    title = f"Predicho vs real - {model_name}"
    if test_year is not None:
        title += f" ({test_year})"

    ax.set_title(title)
    ax.set_xlabel("Valor real")
    ax.set_ylabel("Valor predicho")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig, ax

# ================================== 
# DEF plot_error_distribution(): HISTOGRAMA DE ERRORES PARA DIAGNÓSTICO DE MODELO
# ==================================    
def plot_error_distribution(
    predictions_df: pd.DataFrame,
    model_name: str,
    test_year: int | None = None,
    bins: int = 40,
    figsize: tuple[int, int] = (6.5, 4),
) -> tuple[plt.Figure, plt.Axes]:
    """
    Histograma de errores: y_pred - y_true.
        Recibe:
            - predictions_df: DataFrame con las predicciones.
            - model_name: Nombre del modelo.
            - test_year: Año de prueba.
            - bins: Número de bins para el histograma (40 por defecto).
            - figsize: Tamaño de la figura.
        Devuelve:
            - fig, ax: Figura y ejes del plot.
    """
    required_cols = ["model", "error"]
    validate_required_columns(predictions_df, required_cols, context="diagnostics")

    df = predictions_df[predictions_df["model"] == model_name].copy()

    if test_year is not None:
        validate_required_columns(df, ["test_year"], context="diagnostics")
        df = df[df["test_year"] == test_year].copy()

    if df.empty:
        raise ValueError("No hay datos para el modelo/año solicitado.")

    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(df["error"].dropna(), bins=bins)

    ax.axvline(0, linestyle="--", linewidth=1.5)

    title = f"Distribución de errores - {model_name}"
    if test_year is not None:
        title += f" ({test_year})"

    ax.set_title(title)
    ax.set_xlabel("Error = predicho - real")
    ax.set_ylabel("Frecuencia")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig, ax

# ================================== 
# DEF build_error_map_frame(): UNE PREDICCIONES CON GEOMETRÍAS PARA MAPEAR EL ERROR MUNICIPAL
# ==================================
def build_error_map_frame(
    predictions_df: pd.DataFrame,
    gdf_municipios: gpd.GeoDataFrame,
    model_name: str,
    test_year: int,
) -> gpd.GeoDataFrame:
    """
    Une predicciones con geometrías para mapear el error municipal
        Recibe:
            - predictions_df: DataFrame con las predicciones.
            - gdf_municipios: GeoDataFrame con las geometrías municipales y columna CVEGEO.
            - model_name: Nombre del modelo.
            - test_year: Año de prueba.
        Devuelve:
            - GeoDataFrame con geometrías municipales y columnas de predicción/error para diagnóstico espacial.
    """
    required_cols = ["model", "test_year", "CVEGEO", "municipio", "y_true", "y_pred", "error", "abs_error"]
    validate_required_columns(
        predictions_df, 
        required_cols,
        context="diagnostics",
    )

    validate_required_columns(
        gdf_municipios,
        ["CVEGEO", "geometry"],
        context="diagnostics",
    )

    pred = predictions_df[
        (predictions_df["model"] == model_name)
        & (predictions_df["test_year"] == test_year)
    ].copy()

    if pred.empty:
        raise ValueError("No hay predicciones para el modelo/año solicitado.")

    pred["CVEGEO"] = pred["CVEGEO"].astype(str)

    gdf = gdf_municipios.copy()
    gdf["CVEGEO"] = gdf["CVEGEO"].astype(str)

    merged = gdf.merge(
        pred[["CVEGEO", "municipio", "y_true", "y_pred", "error", "abs_error"]],
        on="CVEGEO",
        how="left",
        validate="1:1",
    )

    return merged

# ==================================
# DEF build_error_choropleth_plotly(): MAPA COROPLÉTICO INTERACTIVO DEL ERROR MUNICIPAL
# ==================================    
def build_error_choropleth_plotly(
    gdf_error: gpd.GeoDataFrame,
    color_col: str = "error",
    title: str | None = None,
    width: int = 1000,
    height: int = 520,
):
    """
    Genera un mapa coroplético interactivo del error municipal usando Plotly.
        Recibe:
            - gdf_error: GeoDataFrame con geometrías municipales y columnas de error/predicción.
            - color_col: Columna a usar para colorear el mapa ("error" o "abs_error").
            - title: Título del mapa (opcional).
            - width: Ancho del mapa en píxeles.
            - height: Alto del mapa en píxeles.
        Devuelve:
            - fig: Figura de Plotly con el mapa coroplético del error municipal.
    """
    valid_cols = {"error", "abs_error"}

    if color_col not in valid_cols:
        raise ValueError(f"color_col debe ser una de {valid_cols}")

    required_cols = ["CVEGEO", "geometry", "y_true", "y_pred", "error", "abs_error"]
    validate_required_columns(gdf_error, required_cols, context="diagnostics")

    plot_gdf = gdf_error.copy()

    if plot_gdf.crs is None:
        raise ValueError("El GeoDataFrame no tiene CRS definido.")

    plot_gdf = plot_gdf[plot_gdf.geometry.notna()].copy()
    plot_gdf = plot_gdf.to_crs(epsg=4326)
    plot_gdf = plot_gdf.explode(index_parts=False).reset_index(drop=True)

    plot_gdf["feature_id"] = plot_gdf["CVEGEO"].astype(str)

    if "municipio" in plot_gdf.columns:
        municipio_base = plot_gdf["municipio"]
    elif "NOMGEO" in plot_gdf.columns:
        municipio_base = plot_gdf["NOMGEO"]
    else:
        raise ValueError("Se requiere 'municipio' o 'NOMGEO' para el hover del mapa.")

    plot_gdf["municipio_label"] = municipio_base.astype("string")

    geojson_dict = json.loads(
        plot_gdf[["feature_id", "geometry"]].to_json()
    )

    for feature, fid in zip(geojson_dict["features"], plot_gdf["feature_id"]):
        feature["id"] = fid

    if color_col == "error":
        color_scale = "RdBu"
        abs_error_series = np.abs(plot_gdf["error"].dropna())

        if abs_error_series.empty:
            raise ValueError("No hay valores válidos en 'error' para construir el mapa.")

        range_bound = float(abs_error_series.max())
        range_color = (-range_bound, range_bound)

        if title is None:
            title = "Error municipal del modelo"

        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Real: %{customdata[0]:.3f}<br>"
            "Predicho: %{customdata[1]:.3f}<br>"
            "Error: %{customdata[2]:.3f}<br>"
            "Error absoluto: %{customdata[3]:.3f}"
            "<extra></extra>"
        )
    else:
        color_scale = "OrRd"
        range_color = None

        if title is None:
            title = "Error absoluto municipal del modelo"

        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Real: %{customdata[0]:.3f}<br>"
            "Predicho: %{customdata[1]:.3f}<br>"
            "Error: %{customdata[2]:.3f}<br>"
            "Error absoluto: %{customdata[3]:.3f}"
            "<extra></extra>"
        )

    fig = px.choropleth(
        plot_gdf,
        geojson=geojson_dict,
        locations="feature_id",
        featureidkey="id",
        color=color_col,
        color_continuous_scale=color_scale,
        range_color=range_color,
        hover_name="municipio_label",
        custom_data=["y_true", "y_pred", "error", "abs_error"],
    )

    fig.update_geos(
        fitbounds="geojson",
        visible=False,
    )

    fig.update_traces(
        marker_line_color="black",
        marker_line_width=0.4,
        hovertemplate=hovertemplate,
    )

    fig.update_layout(
        title=dict(
            text=title,
            x=0.02,
            xanchor="left",
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        width=width,
        height=height,
    )

    return fig