"""
materialization.py
Módulo offline para construir y guardar artefactos procesados
listos para consumo por la aplicación.
"""

# ---------------------------------------
# IMPORTACIONES
# ---------------------------------------
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.base.artifact_loader import ensure_processed_app_dir
from src.base.config import PROJECT_ROOT, SHAPEFILE_PATH
from src.base.constants import AVAILABLE_YEARS, STATE_LABELS
from src.offline.base.aggregations import aggregate_group_year
from src.offline.base.pipeline import load_processed_multi_year, load_processed_year
from src.offline.forecast_intervals import add_prediction_interval_from_oos_error
from src.offline.maps_build import (
    build_municipal_metrics,
    load_municipal_geometries,
)
from src.offline.modeling.pipeline import (
    build_forecast_2027_outputs,
    run_model_diagnostics,
)
from src.offline.view_models import (
    get_group_year_view,
    get_state_year_view,
    get_view,
)

# ---------------------------------------
# MAPEO DE CÓDIGOS ESTATALES NUMÉRICOS -> CANÓNICOS
# ---------------------------------------
STATE_CODE_FROM_CVE_ENT: dict[str, str] = {
    "01": "ags",
    "02": "bc",
    "03": "bcs",
    "04": "camp",
    "05": "coah",
    "06": "col",
    "07": "chis",
    "08": "chih",
    "09": "cdmx",
    "10": "dgo",
    "11": "gto",
    "12": "gro",
    "13": "hgo",
    "14": "jal",
    "15": "mex",
    "16": "mich",
    "17": "mor",
    "18": "nay",
    "19": "nl",
    "20": "oax",
    "21": "pue",
    "22": "qro",
    "23": "qroo",
    "24": "slp",
    "25": "sin",
    "26": "son",
    "27": "tab",
    "28": "tam",
    "29": "tlax",
    "30": "ver",
    "31": "yuc",
    "32": "zac",
}


# =====================================================
# HELPERS DE RUTA / IO
# =====================================================
def _artifact_path(filename: str) -> Path:
    """
    Construye la ruta absoluta al artefacto solicitado.
    """
    return ensure_processed_app_dir() / filename


def save_dataframe_artifact(df: pd.DataFrame, filename: str) -> Path:
    """
    Guarda un DataFrame como artefacto parquet.
    """
    path = _artifact_path(filename)
    df.to_parquet(path, index=False)
    return path


def save_geodataframe_artifact(gdf: gpd.GeoDataFrame, filename: str) -> Path:
    """
    Guarda un GeoDataFrame como artefacto parquet.
    """
    path = _artifact_path(filename)
    gdf.to_parquet(path, index=False)
    return path


# =====================================================
# MATERIALIZACIÓN DE TABLAS PARA TAB_ESTADO / EXPLORADOR
# =====================================================
def build_tab_estado_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> dict[str, pd.DataFrame]:
    """
    Construye tablas agregadas listas para la exploración estatal.
    En la versión actual de la app solo se materializa la vista por municipio.
    """
    artifacts: dict[str, list[pd.DataFrame]] = {
        "tab_estado_municipio.parquet": [],
    }

    for year in years:
        df_year = load_processed_year(PROJECT_ROOT, year=year)
        state_codes = sorted(df_year["state_code"].dropna().astype(str).unique())

        for state_code in state_codes:
            df_state = df_year[df_year["state_code"] == state_code].copy()

            view = get_view(
                df_state,
                grouping_label="Mostrar por municipio",
            ).copy()
            view["year"] = int(year)
            view["state_code"] = state_code
            artifacts["tab_estado_municipio.parquet"].append(view)

    out: dict[str, pd.DataFrame] = {}
    for filename, parts in artifacts.items():
        out[filename] = pd.concat(parts, ignore_index=True)

    return out


def save_tab_estado_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> list[Path]:
    """
    Construye y guarda artefactos agregados por estado.
    """
    artifacts = build_tab_estado_artifacts(years=years)
    paths: list[Path] = []

    for filename, df in artifacts.items():
        paths.append(save_dataframe_artifact(df, filename))

    return paths


# =====================================================
# MATERIALIZACIÓN DE TABLA PARA MAPA MUNICIPAL
# =====================================================
def build_tab_estado_mapa_artifact(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> pd.DataFrame:
    """
    Construye la tabla agregada municipal lista para mapas por año + estado + municipio.
    """
    parts: list[pd.DataFrame] = []

    for year in years:
        df_year = load_processed_year(PROJECT_ROOT, year=year)
        state_codes = sorted(df_year["state_code"].dropna().astype(str).unique())

        for state_code in state_codes:
            df_state = df_year[df_year["state_code"] == state_code].copy()
            df_mun = build_municipal_metrics(df_state).copy()
            df_mun["year"] = int(year)
            df_mun["state_code"] = state_code
            parts.append(df_mun)

    return pd.concat(parts, ignore_index=True)


def save_tab_estado_mapa_artifact(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> Path:
    """
    Construye y guarda el artefacto tabular del mapa municipal.
    """
    df = build_tab_estado_mapa_artifact(years=years)
    return save_dataframe_artifact(df, "tab_estado_mapa.parquet")


# =====================================================
# MATERIALIZACIÓN DE GEOMETRÍA MUNICIPAL
# =====================================================
def build_geometry_artifact() -> gpd.GeoDataFrame:
    """
    Construye el artefacto geoespacial base de municipios.
    """
    return load_municipal_geometries(SHAPEFILE_PATH).copy()


def save_geometry_artifact() -> Path:
    """
    Guarda el artefacto geoespacial completo de municipios.
    """
    gdf = build_geometry_artifact()
    return save_geodataframe_artifact(gdf, "municipios_geometry.parquet")


def build_geometry_simplified_artifact(
    tolerance: float = 500,
) -> gpd.GeoDataFrame:
    """
    Construye un artefacto geoespacial simplificado de municipios
    para visualización más ligera en la app.
    """
    gdf = load_municipal_geometries(SHAPEFILE_PATH).copy()
    gdf["geometry"] = gdf["geometry"].simplify(
        tolerance=tolerance,
        preserve_topology=True,
    )
    return gdf


def save_geometry_simplified_artifact(
    tolerance: float = 500,
) -> Path:
    """
    Guarda el artefacto geoespacial simplificado de municipios.
    """
    gdf = build_geometry_simplified_artifact(tolerance=tolerance)
    return save_geodataframe_artifact(
        gdf,
        "municipios_geometry_simplified.parquet",
    )


# =====================================================
# MATERIALIZACIÓN DE GEOMETRÍA ESTATAL SIMPLIFICADA
# =====================================================
def build_state_geometry_simplified_artifact(
    tolerance: float = 1000,
) -> gpd.GeoDataFrame:
    """
    Construye un artefacto geoespacial simplificado a nivel estado
    a partir de la geometría municipal base.

    El flujo es:
    - cargar geometría municipal desde la fuente geoespacial disponible,
    - homogeneizar claves estatales,
    - disolver por estado,
    - simplificar de forma conservadora.
    """
    gdf = load_municipal_geometries(SHAPEFILE_PATH).copy()

    if "CVE_ENT" not in gdf.columns:
        raise ValueError("La geometría municipal no contiene la columna 'CVE_ENT'.")

    gdf["CVE_ENT"] = gdf["CVE_ENT"].astype(str).str.zfill(2)
    gdf["state_code"] = gdf["CVE_ENT"].map(STATE_CODE_FROM_CVE_ENT)

    missing_codes = gdf[gdf["state_code"].isna()]["CVE_ENT"].drop_duplicates().tolist()
    if missing_codes:
        raise ValueError(
            f"No se pudo mapear CVE_ENT a state_code para: {missing_codes}"
        )

    gdf["state_label"] = gdf["state_code"].map(STATE_LABELS).fillna(gdf["state_code"])

    gdf_states = (
        gdf[["state_code", "state_label", "geometry"]]
        .dissolve(by=["state_code", "state_label"], as_index=False)
        .copy()
    )

    gdf_states["geometry"] = gdf_states["geometry"].simplify(
        tolerance=tolerance,
        preserve_topology=True,
    )

    return gdf_states


def save_state_geometry_simplified_artifact(
    tolerance: float = 1000,
) -> Path:
    """
    Guarda el artefacto geoespacial simplificado de estados.
    """
    gdf = build_state_geometry_simplified_artifact(tolerance=tolerance)
    return save_geodataframe_artifact(
        gdf,
        "estados_geometry_simplified.parquet",
    )


# =====================================================
# MATERIALIZACIÓN DE TABLAS PARA TAB_AÑOS / EXPLORADOR
# =====================================================
def build_tab_anios_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> dict[str, pd.DataFrame]:
    """
    Construye tablas agregadas listas para series de tiempo nacionales.
    """
    df_all = load_processed_multi_year(PROJECT_ROOT, years=years)

    return {
        "tab_anios_estado.parquet": get_state_year_view(df_all),
        "tab_anios_sexo.parquet": get_group_year_view(df_all, group_col="sexo"),
        "tab_anios_edad.parquet": get_group_year_view(
            df_all,
            group_col="generacion",
        ),
        "tab_anios_tipo_seccion.parquet": get_group_year_view(
            df_all,
            group_col="tipo_seccion",
        ),
    }


def save_tab_anios_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> list[Path]:
    """
    Construye y guarda artefactos de series temporales nacionales.
    """
    artifacts = build_tab_anios_artifacts(years=years)
    paths: list[Path] = []

    for filename, df in artifacts.items():
        paths.append(save_dataframe_artifact(df, filename))

    return paths


# =====================================================
# MATERIALIZACIÓN DE TABLAS PARA ANÁLISIS ESTATAL POR DIMENSIÓN
# =====================================================
def build_tab_anios_state_dimension_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> dict[str, pd.DataFrame]:
    """
    Construye tablas agregadas para análisis estatal por dimensión.
    Cada tabla queda agregada por estado real + año + categoría interna.
    """
    df_all = load_processed_multi_year(PROJECT_ROOT, years=years)

    artifacts: dict[str, list[pd.DataFrame]] = {
        "tab_anios_estado_sexo.parquet": [],
        "tab_anios_estado_edad.parquet": [],
        "tab_anios_estado_tipo_seccion.parquet": [],
    }

    dimension_map = {
        "tab_anios_estado_sexo.parquet": "sexo",
        "tab_anios_estado_edad.parquet": "generacion",
        "tab_anios_estado_tipo_seccion.parquet": "tipo_seccion",
    }

    state_codes = sorted(df_all["state_code"].dropna().astype(str).unique())

    for state_code in state_codes:
        df_state = df_all[df_all["state_code"] == state_code].copy()

        for filename, group_col in dimension_map.items():
            view = aggregate_group_year(df_state, group_col=group_col).copy()
            view = view.rename(columns={group_col: "serie_code"})
            view["serie_code"] = view["serie_code"].astype("string")
            view["serie_label"] = view["serie_code"]
            view["state_code"] = state_code
            view["state_label"] = STATE_LABELS.get(state_code, state_code)
            artifacts[filename].append(view)

    out: dict[str, pd.DataFrame] = {}
    for filename, parts in artifacts.items():
        out[filename] = pd.concat(parts, ignore_index=True)

    return out


def save_tab_anios_state_dimension_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> list[Path]:
    """
    Construye y guarda artefactos para análisis estatal por dimensión.
    """
    artifacts = build_tab_anios_state_dimension_artifacts(years=years)
    paths: list[Path] = []

    for filename, df in artifacts.items():
        paths.append(save_dataframe_artifact(df, filename))

    return paths


# =====================================================
# MATERIALIZACIÓN DE OUTPUTS DE MODELADO
# =====================================================
def build_modeling_artifacts() -> dict[str, pd.DataFrame]:
    """
    Construye artefactos listos para la pestaña Modelo predictivo.
    Los pronósticos 2027 quedan materializados con intervalos de
    predicción aproximados.
    """
    (
        _results_df,
        summary_df,
        predictions_df,
        coef_linear,
        coef_ridge,
    ) = run_model_diagnostics(PROJECT_ROOT)

    forecast_linear, forecast_ridge = build_forecast_2027_outputs(PROJECT_ROOT)

    forecast_linear = add_prediction_interval_from_oos_error(
        forecast_df=forecast_linear,
        predictions_df=predictions_df,
        model_name="linear_regression",
    )

    forecast_ridge = add_prediction_interval_from_oos_error(
        forecast_df=forecast_ridge,
        predictions_df=predictions_df,
        model_name="ridge",
    )

    return {
        "model_summary.parquet": summary_df,
        "model_predictions.parquet": predictions_df,
        "model_coef_linear.parquet": coef_linear,
        "model_coef_ridge.parquet": coef_ridge,
        "forecast_linear_2027.parquet": forecast_linear,
        "forecast_ridge_2027.parquet": forecast_ridge,
    }


def save_modeling_artifacts() -> list[Path]:
    """
    Construye y guarda artefactos de modelado.
    """
    artifacts = build_modeling_artifacts()
    paths: list[Path] = []

    for filename, df in artifacts.items():
        paths.append(save_dataframe_artifact(df, filename))

    return paths


# =====================================================
# MATERIALIZACIÓN TOTAL
# =====================================================
def materialize_all_app_assets(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> list[Path]:
    """
    Construye y guarda todos los artefactos necesarios para la app.
    """
    paths: list[Path] = []

    paths.extend(save_tab_estado_artifacts(years=years))
    paths.append(save_tab_estado_mapa_artifact(years=years))
    paths.append(save_geometry_simplified_artifact())
    paths.append(save_state_geometry_simplified_artifact())
    paths.extend(save_tab_anios_artifacts(years=years))
    paths.extend(save_tab_anios_state_dimension_artifacts(years=years))
    paths.extend(save_modeling_artifacts())

    return paths