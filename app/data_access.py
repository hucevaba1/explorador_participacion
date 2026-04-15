"""
data_access.py
CAPA DE ACCESO CACHEADO A LOS DATOS PROCESADOS Y GEOMETRÍAS COMPARTIDAS POR LAS PESTAÑAS DE LA APLICACION
"""
#============================
# IMPORTACIONES
#============================
from __future__ import annotations

import geopandas as gpd
import pandas as pd
import streamlit as st

from src.base.materialization import (
    load_dataframe_artifact,
    load_geodataframe_artifact,
)
#============================
# CARGA CACHEADA
#============================
@st.cache_data(show_spinner=False)
def get_tab_estado_artifact_cached(filename: str) -> pd.DataFrame:
    return load_dataframe_artifact(filename)


@st.cache_data(show_spinner=False)
def get_tab_anios_artifact_cached(filename: str) -> pd.DataFrame:
    return load_dataframe_artifact(filename)


@st.cache_data(show_spinner=False)
def get_model_artifact_cached(filename: str) -> pd.DataFrame:
    return load_dataframe_artifact(filename)


@st.cache_data(show_spinner=False)
def get_municipal_geometries_cached() -> gpd.GeoDataFrame:
    return load_geodataframe_artifact("municipios_geometry_simplified.parquet")
