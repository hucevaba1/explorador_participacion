"""
maps_build.py
Funciones de preparación y construcción de datos geoespaciales
para la capa offline del proyecto.
"""

# ==========================
# IMPORTACIONES
# ==========================
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.offline.base.aggregations import aggregate_group
from src.base.validator import validate_required_columns

#===================================
# CORRECCIÖN DE GEOMTRÏAS BJ
#====================================
MUNICIPAL_CODE_ALIASES: dict[tuple[str, str], str] = {
    ("03", "004"): "009",  # Loreto
    ("03", "005"): "008",  # Los Cabos
}

# -----------------------------------
# DEF load_municipal_geometries(): CARGA EL SHAPEFILE DE GEOMETRÍAS MUNICIPALES Y CREA LA COLUMNA CVEGEO
# -----------------------------------
def load_municipal_geometries(shp_path: str | Path) -> gpd.GeoDataFrame:
    """
    Carga el shapefile de geometrías municipales.

    Recibe:
        - shp_path: ruta al archivo shapefile de geometrías municipales

    Devuelve:
        - GeoDataFrame con columnas:
            - CVE_ENT
            - CVE_MUN
            - CVEGEO
    """
    gdf = gpd.read_file(shp_path)

    validate_required_columns(gdf, ["CVE_ENT", "CVE_MUN"], context="maps")

    gdf["CVE_ENT"] = gdf["CVE_ENT"].astype(str).str.zfill(2)
    gdf["CVE_MUN"] = gdf["CVE_MUN"].astype(str).str.zfill(3)
    gdf["CVEGEO"] = gdf["CVE_ENT"] + gdf["CVE_MUN"]

    return gdf


# -----------------------------------
# DEF build_municipal_metrics(): AGRUPA LOS DATOS POR MUNICIPIO Y CALCULA LAS MÉTRICAS
# -----------------------------------
def build_municipal_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye un DataFrame con métricas municipales a partir del DataFrame original.
    """
    required_cols = ["EDOCVE", "MPIOCVE", "MPIONOM", "SV", "NV", "NS", "LN"]
    validate_required_columns(df, required_cols, context="maps")

    work = df.copy()

    work["EDOCVE"] = work["EDOCVE"].astype("int64").astype(str).str.zfill(2)
    work["MPIOCVE"] = work["MPIOCVE"].astype("int64").astype(str).str.zfill(3)
    work["MPIOCVE"] = [MUNICIPAL_CODE_ALIASES.get((edo, mpio), mpio) for edo, mpio in zip(work["EDOCVE"], work["MPIOCVE"])]
    work["CVEGEO"] = work["EDOCVE"] + work["MPIOCVE"]

    mun_names = (
        work[["CVEGEO", "MPIONOM"]]
        .drop_duplicates(subset=["CVEGEO"])
    )

    agg = (
        aggregate_group(
            work,
            group_col="CVEGEO",
            sv_col="SV",
            nv_col="NV",
            ns_col="NS",
            ln_col="LN",
        )
        .reset_index()
    )

    out = agg.merge(
        mun_names,
        on="CVEGEO",
        how="left",
        validate="1:1",
    )

    return out


# =====================================================
# DEF prepare_state_map_data(): FILTRA ESTADO, CONSTRUYE MÉTRICAS Y UNE GEOMETRÍAS
# =====================================================
def prepare_state_map_data(
    df: pd.DataFrame,
    gdf: gpd.GeoDataFrame,
    state_code_num: int,
) -> gpd.GeoDataFrame:
    """
    Prepara los datos para el mapa de un estado específico.
    """
    validate_required_columns(df, ["EDOCVE"], context="maps")
    validate_required_columns(gdf, ["CVE_ENT", "CVEGEO"], context="maps")

    df_state = df[df["EDOCVE"] == state_code_num].copy()
    df_mun = build_municipal_metrics(df_state)

    state_code_str = str(state_code_num).zfill(2)
    gdf_state = gdf[gdf["CVE_ENT"] == state_code_str].copy()

    gdf_merged = gdf_state.merge(
        df_mun,
        on="CVEGEO",
        how="left",
        validate="1:1",
    )

    return gdf_merged