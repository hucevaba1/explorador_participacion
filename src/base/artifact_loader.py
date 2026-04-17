"""
artifact_loader.py
Módulo encargado de cargar artefactos procesados listos
para consumo por la aplicación.
"""

# ---------------------------------------
# IMPORTACIONES
# ---------------------------------------
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.base.config import PROJECT_ROOT

# ---------------------------------------
# RUTA DE SALIDA DE LAS TABLAS
# ---------------------------------------
PROCESSED_APP_DIR = PROJECT_ROOT / "data" / "processed" / "app"


# =====================================================
# HELPERS DE RUTA / IO
# =====================================================
def ensure_processed_app_dir() -> Path:
    """
    Garantiza la existencia del directorio de artefactos procesados
    para la aplicación y devuelve su ruta.
    """
    PROCESSED_APP_DIR.mkdir(parents=True, exist_ok=True)
    return PROCESSED_APP_DIR


def _artifact_path(filename: str) -> Path:
    """
    Construye la ruta absoluta al artefacto solicitado.
    """
    return ensure_processed_app_dir() / filename


def load_dataframe_artifact(filename: str) -> pd.DataFrame:
    """
    Carga un artefacto tabular en formato parquet.
    """
    path = _artifact_path(filename)

    if not path.exists():
        raise FileNotFoundError(f"No existe el artefacto procesado: {path}")

    return pd.read_parquet(path)


def load_geodataframe_artifact(filename: str) -> gpd.GeoDataFrame:
    """
    Carga un artefacto geoespacial en formato parquet.
    """
    path = _artifact_path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el artefacto geoespacial procesado: {path}"
        )

    return gpd.read_parquet(path)