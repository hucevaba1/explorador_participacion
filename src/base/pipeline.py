"""
pipeline.py
# ARCHIVO DE PIPELINE OFFLINE PARA EL PROYECTO DE ANÁLISIS DE DATOS ELECTORALES:
# Este módulo se encarga de orquestar el proceso completo de carga, limpieza, optimización y transformación de los datos. 
# Incluye funciones para:
# - Cargar y procesar todo el conjunto de datos para los años seleccionados
# - Cargar y procesar un año específico para todos los estados o un subconjunto de estados
# - Cargar y procesar todas las elecciones de un estado específico para los años seleccionados
# - Alias explícito para carga multianual o series temporales
# Cada función devuelve un DataFrame listo para análisis y visualización, con las optimizaciones y transformaciones aplicadas.
"""

#------------------------------------
# IMPORTACIONES
#------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from src.base.data_loader import (
    load_data,
    load_state_data,
    load_year_data,
)
from src.base.data_cleaning import optimize_types
from src.base.transformations import standardize_dimensions

#--------------------------------------------------------------------
# DEF prepare_dataframe(): PREPARA EL DATAFRAME APLICANDO OPTIMIZACIÓN DE TIPOS Y ESTANDARIZACIÓN DE DIMENSIONES DERIVADAS
#--------------------------------------------------------------------
def prepare_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica optimización de tipos y estandarización de dimensiones derivadas.
    Recibe:
        - df_raw: DataFrame sin procesar cargado desde los archivos CSV.
    Devuelve:
        - DataFrame procesado, listo para análisis y visualización.
    """
    df = optimize_types(df_raw)
    df = standardize_dimensions(df)
    return df

#--------------------------------------------------------------------
# DEF load_processed_data(): CARGA TODOS LOS DATOS PARA LOS AÑOS INDICADOS Y DEVUELVE UN DATAFRAME PROCESADO
#--------------------------------------------------------------------
def load_processed_data(
    base_dir: Path,
    years: Iterable[int] = (2009, 2012, 2015, 2018, 2021, 2024),
) -> pd.DataFrame:
    """
    Carga todos los datos para los años indicados y devuelve un DataFrame procesado.
    Recibe:
            - base_dir: ruta raíz del proyecto
            - years: años a cargar (default: todos)
    Devuelve:
            - Un DataFrame con todos los datos concatenados, optimizados y con dimensiones derivadas estandarizadas, listo para análisis y visualización    
    """
    df_raw = load_data(base_dir=base_dir, years=years) #CARGA LOS DATOS SIN PROCESAR
    return prepare_dataframe(df_raw) #APLICA def prepare_dataframe()

#--------------------------------------------------------------------
# DEF load_processed_year(): CARGA UN AÑO ESPECÍFICO PARA UNO, ALGUNO O TODOS LOS ESTADOS Y DEVUELVE UN DATAFRAME PROCESADO
#--------------------------------------------------------------------
def load_processed_year(
    base_dir: Path,
    year: int,
    states: Iterable[str] | None = None,
    strict_states: bool = True,
) -> pd.DataFrame:
    """
    Carga un año específico para uno, alguno o todos los estados y devuelve un DataFrame procesado.
    Recibe:
            - base_dir: ruta raíz del proyecto
            - year: año a cargar (default: 2024)
            - states: estados a cargar (default: todos)
            - strict_states: si True, lanza un error si se especifica un estado que no se encuentra en los archivos (default: True)
    Devuelve:
            - Un DataFrame con los datos del año y estados especificados, optimizados y con dimensiones derivadas estandarizadas, listo para análisis y visualización    
    """
    df_raw = load_year_data(
        base_dir=base_dir,
        year=year,
        states=states,
        strict_states=strict_states,
    )
    return prepare_dataframe(df_raw) #APLICA def prepare_dataframe() A df_raw CARGADO CON load_year_data()

#--------------------------------------------------------------------
# DEF load_processed_state(): CARGA UN ESTADO ESPECÍFICO PARA UNO O VARIOS AÑOS Y DEVUELVE UN DATAFRAME PROCESADO
#--------------------------------------------------------------------
def load_processed_state(
    base_dir: Path,
    state_code: str,
    years: Iterable[int] = (2009, 2012, 2015, 2018, 2021, 2024),
) -> pd.DataFrame:
    """
    Carga un estado específico para uno o varios años y devuelve un DataFrame procesado.
    Recibe:
            - base_dir: ruta raíz del proyecto
            - state_code: código del estado a cargar (ej. "ags", "cdmx")
            - years: años a cargar (default: todos)
    Devuelve:
            - Un DataFrame con los datos del estado y años especificados, optimizados y con dimensiones derivadas estandarizadas, listo para análisis y visualización     
    """
    df_raw = load_state_data(
        base_dir=base_dir,
        state_code=state_code,
        years=years,
    )
    return prepare_dataframe(df_raw) #APLICA def prepare_dataframe() A df_raw CARGADO CON load_state_data()

#--------------------------------------------------------------------
# DEF load_processed_multi_year(): ALIAS EXPLÍCITO PARA SERIES TEMPORALES O ANÁLISIS MULTIANUALES
#--------------------------------------------------------------------
def load_processed_multi_year(
    base_dir: Path,
    years: Iterable[int] = (2009, 2012, 2015, 2018, 2021, 2024),
) -> pd.DataFrame:
    """
    Alias explícito para cargar datos de múltiples años.
    Recibe:
            - base_dir: ruta raíz del proyecto
            - years: años a cargar (ej. (2012, 2015, 2018))
    Devuelve:
            - Un DataFrame con los datos de los años especificados, optimizados y con dimensiones derivadas estandarizadas, listo para análisis y visualización    
    """
    return load_processed_data(base_dir=base_dir, years=years) #APLICA def load_processed_data() PARA LOS AÑOS ESPECIFICADOS 