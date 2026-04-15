''' 
data_cleaning.py
# ARCHIVO DE LIMPIEZA DE DATOS PARA EL PROYECTO DE ANÁLISIS DE DATOS ELECTORALES:
# Este módulo se encarga de limpiar y optimizar los datos cargados desde los archivos CSV. 
# Incluye funciones para:
# - Convertir tipos de datos
# - Manejar valores faltantes
# - Preparar los datos para análisis posteriores
'''

# --------------------------------
# IMPORTACIONES
# --------------------------------
from __future__ import annotations
import pandas as pd

# =====================================================
# DEF optimize_types(): OPTIMIZA LOS TIPOS DE DATOS DE LAS COLUMNAS DEL DATAFRAME PARA MEJORAR EL RENDIMIENTO Y REDUCIR EL USO DE MEMORIA
# De int64 a Int32
# De object a category y
# De object a datetime según corresponda
# ===================================================== 
def optimize_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimiza los tipos de datos del DataFrame para reducir uso de memoria
    y mejorar el rendimiento en pasos posteriores del pipeline.

    Reglas aplicadas:
    - Convierte columnas numéricas enteras a Int32 cuando existen.
    - Convierte columnas nominales seleccionadas a category.
    - Convierte FELECCION a datetime cuando existe.

    Recibe:
        - df: DataFrame a optimizar

    Devuelve:
        - DataFrame con tipos optimizados
    """
    out = df.copy()

    int_cols = [
        "SV",
        "NV",
        "LN",
        "NS",
        "EDAD",
        "SEXO",
        "EDOCVE",
        "MPIOCVE",
        "SECCION",
        "year",
        "AELEC",
        "DEL",
        "DEF",
    ]

    for col in int_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int32")

    cat_cols = [
        "EDONOM",
        "MPIONOM",
        "TIPOSEC",
        "state_code",
    ]

    for col in cat_cols:
        if col in out.columns:
            out[col] = out[col].astype("category")

    if "FELECCION" in out.columns:
        out["FELECCION"] = pd.to_datetime(out["FELECCION"], errors="coerce")

    return out

