"""
materialization.py
Módulo para construir, guardar y cargar artefactos procesados
listos para consumo por la aplicación.
"""

# ---------------------------------------
# IMPORTACIONES
# ---------------------------------------
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.base.config import PROJECT_ROOT, SHAPEFILE_PATH
from src.base.constants import AVAILABLE_YEARS, STATE_LABELS
from src.base.pipeline import load_processed_multi_year, load_processed_year
from src.views.view_models import (
    get_view,
    get_group_year_view,
    get_state_year_view,
)
from src.modeling.pipeline import (
    run_model_diagnostics,
    build_forecast_2027_outputs,
)
from src.maps.maps import (
    load_municipal_geometries,
    build_municipal_metrics,
)
from src.base.aggregations import aggregate_group_year
# ---------------------------------------
# RUTA DE SALIDA DE LAS TABLAS
# ---------------------------------------
PROCESSED_APP_DIR = PROJECT_ROOT / "data" / "processed" / "app"


# =====================================================
# HELPERS DE RUTA / IO
# =====================================================
def ensure_processed_app_dir() -> Path:
    PROCESSED_APP_DIR.mkdir(parents=True, exist_ok=True)
    return PROCESSED_APP_DIR


def _artifact_path(filename: str) -> Path:
    return ensure_processed_app_dir() / filename


def save_dataframe_artifact(df: pd.DataFrame, filename: str) -> Path:
    path = _artifact_path(filename)
    df.to_parquet(path, index=False)
    return path


def load_dataframe_artifact(filename: str) -> pd.DataFrame:
    path = _artifact_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"No existe el artefacto procesado: {path}")
    return pd.read_parquet(path)


def save_geodataframe_artifact(gdf: gpd.GeoDataFrame, filename: str) -> Path:
    path = _artifact_path(filename)
    gdf.to_parquet(path, index=False)
    return path


def load_geodataframe_artifact(filename: str) -> gpd.GeoDataFrame:
    path = _artifact_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"No existe el artefacto geoespacial procesado: {path}")
    return gpd.read_parquet(path)


# =====================================================
# MATERIALIZACIÓN DE TABLAS PARA TAB_ESTADO
# =====================================================
def build_tab_estado_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> dict[str, pd.DataFrame]:
    """
    Construye tablas agregadas listas para la pestaña Por estado.
    Cada tabla queda agregada por año + estado + categoría.
    """
    artifacts: dict[str, list[pd.DataFrame]] = {
        "tab_estado_municipio.parquet": [],
        "tab_estado_sexo.parquet": [],
        "tab_estado_edad.parquet": [],
        "tab_estado_tipo_seccion.parquet": [],
    }

    grouping_map = {
        "tab_estado_municipio.parquet": "Mostrar por municipio",
        "tab_estado_sexo.parquet": "Mostrar por sexo",
        "tab_estado_edad.parquet": "Mostrar por edad",
        "tab_estado_tipo_seccion.parquet": "Mostrar por tipo de sección",
    }

    for year in years:
        df_year = load_processed_year(PROJECT_ROOT, year=year)

        state_codes = sorted(df_year["state_code"].dropna().astype(str).unique())

        for state_code in state_codes:
            df_state = df_year[df_year["state_code"] == state_code].copy()

            for filename, grouping_label in grouping_map.items():
                view = get_view(df_state, grouping_label=grouping_label).copy()
                view["year"] = int(year)
                view["state_code"] = state_code
                artifacts[filename].append(view)

    out: dict[str, pd.DataFrame] = {}
    for filename, parts in artifacts.items():
        out[filename] = pd.concat(parts, ignore_index=True)

    return out


def save_tab_estado_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> list[Path]:
    artifacts = build_tab_estado_artifacts(years=years)
    paths = []

    for filename, df in artifacts.items():
        paths.append(save_dataframe_artifact(df, filename))

    return paths


# =====================================================
# MATERIALIZACIÓN DE TABLA PARA MAPA DE TAB_ESTADO
# =====================================================
def build_tab_estado_mapa_artifact(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> pd.DataFrame:
    """
    Construye la tabla agregada municipal lista para la pestaña de mapa
    por año + estado + municipio.
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
    df = build_tab_estado_mapa_artifact(years=years)
    return save_dataframe_artifact(df, "tab_estado_mapa.parquet")


# =====================================================
# MATERIALIZACIÓN DE GEOMETRÍA MUNICIPAL
# =====================================================
def build_geometry_artifact() -> gpd.GeoDataFrame:
    """
    Construye el artefacto geoespacial base de municipios.
    """
    gdf = load_municipal_geometries(SHAPEFILE_PATH).copy()
    return gdf


def save_geometry_artifact() -> Path:
    gdf = build_geometry_artifact()
    return save_geodataframe_artifact(gdf, "municipios_geometry.parquet")

# =====================================================
# MATERIALIZACIÓN DE GEOMETRÍA MUNICIPAL | LO MISMO, PERO SIMPLIFICADO
# =====================================================
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
    gdf = build_geometry_simplified_artifact(tolerance=tolerance)
    return save_geodataframe_artifact(
        gdf,
        "municipios_geometry_simplified.parquet",
    )

# =====================================================
# MATERIALIZACIÓN DE TABLAS PARA TAB_AÑOS
# =====================================================
def build_tab_anios_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> dict[str, pd.DataFrame]:
    """
    Construye tablas agregadas listas para la pestaña Por años.
    """
    df_all = load_processed_multi_year(PROJECT_ROOT, years=years)

    artifacts = {
        "tab_anios_estado.parquet": get_state_year_view(df_all),
        "tab_anios_sexo.parquet": get_group_year_view(df_all, group_col="sexo"),
        "tab_anios_edad.parquet": get_group_year_view(df_all, group_col="generacion"),
        "tab_anios_tipo_seccion.parquet": get_group_year_view(df_all, group_col="tipo_seccion"),
    }

    return artifacts


def save_tab_anios_artifacts(
    years: tuple[int, ...] = tuple(int(y) for y in AVAILABLE_YEARS),
) -> list[Path]:
    artifacts = build_tab_anios_artifacts(years=years)
    paths = []

    for filename, df in artifacts.items():
        paths.append(save_dataframe_artifact(df, filename))

    return paths


# =====================================================
# MATERIALIZACIÓN DE OUTPUTS DE MODELADO
# =====================================================
def build_modeling_artifacts() -> dict[str, pd.DataFrame]:
    """
    Construye artefactos listos para la pestaña Modelo predictivo.
    """
    (
        _results_df,
        summary_df,
        predictions_df,
        coef_linear,
        coef_ridge,
    ) = run_model_diagnostics(PROJECT_ROOT)

    forecast_linear, forecast_ridge = build_forecast_2027_outputs(PROJECT_ROOT)

    artifacts = {
        "model_summary.parquet": summary_df,
        "model_predictions.parquet": predictions_df,
        "model_coef_linear.parquet": coef_linear,
        "model_coef_ridge.parquet": coef_ridge,
        "forecast_linear_2027.parquet": forecast_linear,
        "forecast_ridge_2027.parquet": forecast_ridge,
    }

    return artifacts


def save_modeling_artifacts() -> list[Path]:
    artifacts = build_modeling_artifacts()
    paths = []

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
    artifacts = build_tab_anios_state_dimension_artifacts(years=years)
    paths = []

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
    paths.append(save_geometry_artifact())
    paths.extend(save_tab_anios_artifacts(years=years))
    paths.extend(save_tab_anios_state_dimension_artifacts(years=years))
    paths.extend(save_modeling_artifacts())
    paths.append(save_geometry_artifact())
    paths.append(save_geometry_simplified_artifact())

    return paths