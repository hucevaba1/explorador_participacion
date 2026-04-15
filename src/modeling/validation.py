"""
validation.py
ARCHIVO PARA VALIDACIÓN DE MODELOS PARA EL PROYECTO ELECTORAL:
Este módulo proporciona funciones para validar modelos utilizando folds temporales fijos.
Se definen folds específicos para elecciones pasadas, lo que permite evaluar el rendimiento del modelo en datos futuros.
"""

#----------------------------------------
# IMPORTACIONES
#----------------------------------------
from __future__ import annotations
import pandas as pd

from src.base.validator import validate_required_columns

# =====================================================
# DEF get_fixed_time_folds(): GENERA FOLDS TEMPORALES FIJOS PARA VALIDACIÓN 
# =====================================================
def get_fixed_time_folds() -> list[dict[str, list[int] | int]]:
    """
    Devuelve una lista de folds temporales fijos para validación de modelos electorales. 
    Cada fold especifica los años de entrenamiento y el año de prueba. 
        Devuelve:
            Lista de diccionarios con los años de entrenamiento y el año de prueba para cada fold.  
    """
    return [
        {"train_years": [2009, 2012, 2015], "test_year": 2018},
        {"train_years": [2009, 2012, 2015, 2018], "test_year": 2021},
    ]

#=====================================================
# DEF split_fold(): DIVIDE LOS DATOS EN FOLD DE ENTRENAMIENTO Y PRUEBA SEGÚN LOS FOLDS TEMPORALES FIJOS  
#=====================================================
def split_fold(
    df: pd.DataFrame,
    train_years: list[int],
    test_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide el DataFrame en conjuntos de entrenamiento y prueba según los años especificados.
        Recibe:
            df: DataFrame que contiene los datos electorales con una columna 'year' que indica el año de cada registro.
            train_years: Lista de años que se utilizarán para el entrenamiento del modelo.
            test_year: Año que se utilizará para la prueba del modelo.
        Devuelve:
            Tuple con dos DataFrames: el primero para entrenamiento y el segundo para prueba.
    """
    validate_required_columns(
        df,
        ["year"],
        context="validation")

    train = df[df["year"].isin(train_years)].copy()
    test = df[df["year"] == test_year].copy()

    return train, test

