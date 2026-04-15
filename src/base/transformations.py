"""
transformations.py
# ARCHIVO DE TRANSFORMACIONES PARA EL PROYECTO DE ANÁLISIS DE DATOS ELECTORALES:
# Este módulo se encarga de realizar las transformaciones necesarias para el análisis de los datos electorales. Incluye funciones para:
# - Crear dimensiones derivadas a partir de las columnas originales: grupos de edad, etiquetas de sexo y tipo de sección
# - Estandarizar todas las dimensiones derivadas en un solo paso para facilitar su uso en análisis posteriores
"""
# --------------------------------
# IMPORTACIONES
# --------------------------------  
from __future__ import annotations
import pandas as pd

#=====================================================
# DEF _validate_columns_exists(): Sólo para garantizar que las columnas existan
#=====================================================
def _validate_column_exists(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        raise ValueError(f"La columna requerida {col!r} no existe en el DataFrame.")
    
#--------------------------------------------------------------------
# DEF add_age_group(): AÑADE UNA COLUMNA DE GRUPOS DE EDAD (generacion) A PARTIR DE LA COLUMNA DE EDAD (EDAD)
#--------------------------------------------------------------------
def add_age_group(
    df: pd.DataFrame,
    age_col: str = "EDAD",
    out_col: str = "generacion",
) -> None:
    """
    Añade una columna de grupos de edad (generacion) a partir de la columna de edad (EDAD).
    Recibe: 
            - df: DataFrame al que se le añadirá la columna de grupos de edad
            - age_col: nombre de la columna de edad en el DataFrame (default: "EDAD")
            - out_col: nombre de la nueva columna de grupos de edad que se añadirá al DataFrame (default: "generacion")
    Devuelve:
            - None (la función modifica el DataFrame original añadiendo la nueva columna)
    """     
    _validate_column_exists(df, age_col)

    bins = [17, 29, 44, 64, float("inf")]
    labels = ["Joven (18-29)", "Adulto joven (30-44)", "Adulto (45-64)", "Adulto mayor (65+)"]

    df[out_col] = pd.cut(df[age_col], bins=bins, labels=labels).astype("category")    

#--------------------------------------------------------------------
# DEF add_sex_label(): AÑADE UNA COLUMNA DE ETIQUETAS DE SEXO A PARTIR DE LA COLUMNA DE SEXO (SEXO)
#--------------------------------------------------------------------
def add_sex_label(
    df: pd.DataFrame,
    sex_col: str = "SEXO",
    out_col: str = "sexo",
) -> None:
    """
    Añade una columna de etiquetas de sexo a partir de la columna de sexo (SEXO).
    Recibe: 
            - df: DataFrame al que se le añadirá la columna de etiquetas de sexo
            - sex_col: nombre de la columna de sexo en el DataFrame (default: "SEXO")
            - out_col: nombre de la nueva columna de etiquetas de sexo que se añadirá al DataFrame (default: "sexo")
    Devuelve:
            - None (la función modifica el DataFrame original añadiendo la nueva columna)
    """
    _validate_column_exists(df, sex_col) 
    mapping = {0: "Hombre", 1: "Mujer", 2: "No binario"}
    df[out_col] = df[sex_col].map(mapping).astype("category")

#--------------------------------------------------------------------
# DEF add_section_type_label(): AÑADE UNA COLUMNA DE ETIQUETAS DE TIPO DE SECCIÓN A PARTIR DE LA COLUMNA DE TIPO DE SECCIÓN (TIPOSEC)
#--------------------------------------------------------------------
def add_section_type_label(
    df: pd.DataFrame,
    sec_col: str = "TIPOSEC",
    out_col: str = "tipo_seccion",
) -> None:
    """
    Añade una columna de etiquetas de tipo de sección a partir de la columna de tipo de sección (TIPOSEC).
    Recibe: 
            - df: DataFrame al que se le añadirá la columna de etiquetas de tipo de sección
            - sec_col: nombre de la columna de tipo de sección en el DataFrame (default: "TIPOSEC")
            - out_col: nombre de la nueva columna de etiquetas de tipo de sección que se añadirá al DataFrame (default: "tipo_seccion")
    Devuelve:
            - None (la función modifica el DataFrame original añadiendo la nueva columna)
    """     
    _validate_column_exists(df, sec_col) 
    mapping = {"U": "Urbana", "M": "Mixta", "R": "Rural"}
    df[out_col] = df[sec_col].map(mapping).astype("category")

#--------------------------------------------------------------------
# DEF standardize_dimensions(): ESTANDARIZA TODAS LAS DIMENSIONES DERIVADAS EN UN SOLO PASO PARA FACILITAR SU USO EN ANÁLISIS POSTERIORES
#--------------------------------------------------------------------
def standardize_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza todas las dimensiones derivadas en un solo paso para facilitar su uso en análisis posteriores.
    Recibe: 
            - df: DataFrame al que se le añadirán las columnas de dimensiones derivadas
    Devuelve:
            - DataFrame con las columnas de dimensiones derivadas añadidas
    """
    out = df.copy()

    add_age_group(out)
    add_sex_label(out)
    add_section_type_label(out)

    return out