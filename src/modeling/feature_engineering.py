"""
feature_engineering.py
ARCHIVO CON FUNCIONES PARA TRANSFORMAR EL DATASET BASE EN UN DATAFRAME DE CARACTERÍSTICAS PARA MODELADO.
INCLUYE FUNCIONES PARA AGREGAR REZAGOS, PROPORCIONES DE COMPOSICIÓN, CONTEXTO ESTATAL, Y TARGETS DE SIGUIENTE ELECCIÓN.
"""

#----------------------------------
# IMPORRTACIONES
#----------------------------------
from __future__ import annotations

import numpy as np
import pandas as pd

from src.base.validator import validate_required_columns

#-------------------------------------
# DEF _safe_prop(): Mejora propuesta para hacer calculo de proporciones con función auxiliar fuera de otras def
#-------------------------------------
def _safe_prop(
    df: pd.DataFrame,
    num_col: str,
    den_col: str = "LN_total",
) -> pd.Series:
    """
    Calcula proporciones de manera segura, evitando divisiones por cero.
    """
    return np.where(df[den_col] > 0, df[num_col] / df[den_col], np.nan)

#----------------------------------
# DEF biuld_municipio_year_base(): DEVUELVE UN DATAFRAME AGREGADO A NIVEL MUNICIPIO-AÑO CON VARIABLES DE INTERÉS Y PROPORCIONES CALCULADAS.
#----------------------------------
def build_municipio_year_base(
        df: pd.DataFrame
) -> pd.DataFrame:
    """
    Construye un dataframe base a nivel municipio-año con variables de interés y proporciones calculadas.
        Recibe:
            - Dataframe con columnas: state_code, EDOCVE, MPIOCVE, MPIONOM, year, SV, NV, NS, LN.
        Devuelve:
            - Dataframe agregado y proporcione calculadas para el nivel de agregación (municipio-año).
        """
    # VALIDACION
    required_cols = ["state_code", "EDOCVE", "MPIOCVE", "MPIONOM", "year", "SV", "NV", "NS" , "LN",]
    validate_required_columns(df, required_cols, context="feature_engineering")

    # COPIA DE DATASET
    work = df.copy()

    # CAMBIO DE TIPO DE DATOS PARA CLAVES DE AGREGACIÓN 
    work["EDOCVE"] = work["EDOCVE"].astype("Int32")
    work["MPIOCVE"] = work["MPIOCVE"].astype("Int32")

    # CLAVES DE AGREGACIÓN
    keys = ["state_code", "EDOCVE", "MPIOCVE", "MPIONOM", "year"]

    # AGREGACIÓN A NIVEL MUNICIPIO-AÑO PARA VARIABLES DE INTERÉS
    base = (
        work.groupby(
            keys,
            observed=True,
            as_index=False,
        )[["SV", "NV", "NS", "LN"]]
        .sum()
    )

    # CREA CLAVE ÚNICA DE MUNICIPIO (CVEGEO)
    base["CVEGEO"] = (
        base["EDOCVE"].astype("Int64").astype(str).str.zfill(2)
        + base["MPIOCVE"].astype("Int64").astype(str).str.zfill(3)
    )

    # CONVIERTE NOMBRE DE MUNICIPIO A STRING
    base["municipio"] = base["MPIONOM"].astype("string")
    
    # SIGO SIN RECORDAR PARA QUE ESTOY USANDO TOTAL_MARKED PERO LO DEJO.
    base["total_marked"] = base["SV"] + base["NV"]

    # CALCULO DE PROPORCIONES
    base["sv_ratio"] = np.where(base["LN"] > 0, base["SV"] / base["LN"], np.nan)
    base["nv_ratio"] = np.where(base["LN"] > 0, base["NV"] / base["LN"], np.nan)
    base["ns_ratio"] = np.where(base["LN"] > 0, base["NS"] / base["LN"], np.nan)

    return base.sort_values(["CVEGEO", "year"]).reset_index(drop=True)

#----------------------------------
# DEF build_composition_features(): CONSTRUYE PROPORCIONES DE COMPOSICIÓN MUNICIPAL USANDO LN COMO PESO. REQUIERE COLUMNAS DERIVADAS: SEXO, GENERACION, TIPO_SECCION.
#----------------------------------
def build_composition_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye proporciones de composición municipal usando LN como peso. Requiere columnas derivadas: sexo, generacion, tipo_seccion.
        Recibe:
            - Dataframe con columnas: state_code, EDOCVE, MPIOCVE, MPIONOM, year, LN, sexo, generacion, tipo_seccion.
        Devuelve:
            - Dataframe con proporciones de composición municipal para cada categoría de sexo, generación y tipo de sección,
              calculadas como la suma de LN para cada categoría dividida por el total de LN para ese municipio-año.
    """
    # VALIDACION DE COLUMNAS
    required_cols = ["state_code", "EDOCVE", "MPIOCVE", "MPIONOM", "year", "LN", "sexo", "generacion", "tipo_seccion",]
    validate_required_columns(df, required_cols, context= "feature_engineering")

    # HACE COPIA DE DF
    work = df.copy()

    # CLAVES DE TRABAJO
    keys = ["state_code", "EDOCVE", "MPIOCVE", "MPIONOM", "year"]

    # CALCULO DE SUMAS TOTALES DE LN POR MUNICIPIO-AÑO
    total_ln = (
        work.groupby(
            keys,
            observed=True,
            as_index=False)[["LN"]].sum()
            .rename(columns={"LN": "LN_total"})
    )

    # CALCULO DE SUMAS DE LN POR CATEGORÍA DE SEXO, GENERACIÓN Y TIPO DE SECCIÓN, Y PIVOT PARA OBTENER COLUMNAS SEPARADAS PARA CADA CATEGORÍA
    sexo = (
        work.groupby(
            keys + ["sexo"],
            observed=True,
            as_index=False)[["LN"]]
            .sum()
            .pivot(index=keys, columns="sexo", values="LN")
            .reset_index()
    )
    # GARANTIZA QUE LOS NOMBRES DE LAS COLUMNAS SEAN STRING PARA EVITAR PROBLEMAS EN LOS PASOS POSTERIORES
    sexo.columns = [str(c) for c in sexo.columns]

    # LO MISMO, PERO PARA GENERACIÓN
    edad = (
        work.groupby(
            keys + ["generacion"],
            observed=True,
            as_index=False)[["LN"]]
            .sum()
            .pivot(index=keys, columns="generacion", values="LN")
            .reset_index()
    )

    #IGUAL, GARANTIZA QUE LOS NOMBRES DE LAS COLUMNAS SEAN STRING
    edad.columns = [str(c) for c in edad.columns] 

    # LO MISMO, PERO PARA TIPO DE SECCIÓN
    seccion = (
        work.groupby(
            keys + ["tipo_seccion"],
            observed=True,
            as_index=False)[["LN"]]
            .sum()
            .pivot(index=keys, columns="tipo_seccion", values="LN")
            .reset_index()
    )

    #IGUAL, GARANTIZA QUE LOS NOMBRES DE LAS COLUMNAS SEAN STRING
    seccion.columns = [str(c) for c in seccion.columns] 

    # INTEGRA LOS DATAFRAMES DE SUMAS TOTALES Y POR CATEGORÍA EN UN SOLO DATAFRAME PARA CALCULAR PROPORCIONES
    out = total_ln.merge(sexo, on=keys, how="left")
    out = out.merge(edad, on=keys, how="left")
    out = out.merge(seccion, on=keys, how="left")

    # CONVIERTE LAS COLUMNAS DE VALORES A NUMÉRICAS, REEMPLAZANDO ERRORES CON 0 PARA EVITAR PROBLEMAS EN LOS CÁLCULOS DE PROPORCIONES
    value_cols = [c for c in out.columns if c not in keys]
    out[value_cols] = out[value_cols].apply(pd.to_numeric, errors="coerce").fillna(0)


    # Sexo
    out["prop_hombre"] = _safe_prop(out, "Hombre") if "Hombre" in out.columns else np.nan
    out["prop_mujer"] = _safe_prop(out, "Mujer") if "Mujer" in out.columns else np.nan
    out["prop_no_binario"] = _safe_prop(out, "No binario") if "No binario" in out.columns else np.nan

    # Edad
    out["prop_joven"] = _safe_prop(out, "Joven (18-29)") if "Joven (18-29)" in out.columns else np.nan
    out["prop_adulto_joven"] = _safe_prop(out, "Adulto joven (30-44)") if "Adulto joven (30-44)" in out.columns else np.nan
    out["prop_adulto"] = _safe_prop(out, "Adulto (45-64)") if "Adulto (45-64)" in out.columns else np.nan
    out["prop_adulto_mayor"] = _safe_prop(out, "Adulto mayor (65+)") if "Adulto mayor (65+)" in out.columns else np.nan

    # Tipo de sección
    out["prop_urbana"] = _safe_prop(out, "Urbana") if "Urbana" in out.columns else np.nan
    out["prop_mixta"] = _safe_prop(out, "Mixta") if "Mixta" in out.columns else np.nan
    out["prop_rural"] = _safe_prop(out, "Rural") if "Rural" in out.columns else np.nan

    keep_cols = keys + [c for c in out.columns if c.startswith("prop_")]
    return out[keep_cols].copy()

#----------------------------------
# DEF add_lag_features(): AGREGA REZAGOS Y CAMBIOS POR MUNICIPIO PARA VARIABLES DE INTERÉS Y PROPORCIONES CALCULADAS.
#----------------------------------
def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega rezagos y cambios por municipio.
        Recibe:
            - Dataframe con columnas: CVEGEO, year, SV, NV, NS, LN, sv_ratio, nv_ratio, ns_ratio.
        Devuelve:
            - Dataframe con columnas adicionales de rezagos (lag) y cambios (delta) para las variables de interés y proporciones calculadas, organizadas por municipio (CVEGEO) y año. Incluye rezagos de 1 y 2 años para algunas variables, así como
    """
    #VALIDACION 
    required_cols = ["CVEGEO", "year", "SV", "NV", "NS", "LN", "sv_ratio", "nv_ratio", "ns_ratio",]
    validate_required_columns(df, required_cols, context= "feature_engineering")

    # CREA UNA COPIA ORDENADA DEL DATAFRAME PARA CALCULAR LOS REZAGOS DE MANERA CORRECTA
    out = df.copy().sort_values(["CVEGEO", "year"]).reset_index(drop=True)
    by = out.groupby("CVEGEO", observed=True)

    # LAG DE PROPORCIONES CALCULADAS 
    out["lag_sv_ratio_1"] = by["sv_ratio"].shift(1)
    out["lag_sv_ratio_2"] = by["sv_ratio"].shift(2)
    out["lag_nv_ratio_1"] = by["nv_ratio"].shift(1)
    out["lag_ns_ratio_1"] = by["ns_ratio"].shift(1)

    # LAG DE VARIABLES DE INTERÉS (VALOR NUMÉRICO ABSOLUTO)
    out["lag_SV_1"] = by["SV"].shift(1)
    out["lag_NV_1"] = by["NV"].shift(1)
    out["lag_LN_1"] = by["LN"].shift(1)
    out["lag_LN_2"] = by["LN"].shift(2)

    # CAMBIOS ENTRE REZAGOS (DELTA)
    out["delta_sv_ratio_1"] = out["lag_sv_ratio_1"] - out["lag_sv_ratio_2"]
    out["delta_ln_1"] = out["lag_LN_1"] - out["lag_LN_2"]

    return out

#----------------------------------
# DEF add_state_context_features(): AGREGA CONTEXTO ESTATAL REZAGADO CALCULANDO PROPORCIÓN DE SV A NIVEL ESTATAL Y SU REZAGO PARA CADA MUNICIPIO-AÑO.
#---------------------------------- 
def add_state_context_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega contexto estatal rezagado.
        Recibe:
            - Dataframe con columnas: state_code, year, SV, NV, NS, LN, lag_sv_ratio_1.
        Devuelve:
            - Dataframe con columnas adicionales que representan el contexto estatal rezagado, calculado como la proporción de SV a nivel estatal 
              para cada año y su rezago de 1 año, y la diferencia entre el rezago de la proporción de SV a nivel municipal y el rezago
    """
    #VALIDACIÓN
    required_cols = ["state_code", "year", "SV", "NV", "NS", "LN", "lag_sv_ratio_1",]
    validate_required_columns(df, required_cols, context= "feature_engineering")

    #CREA COPIA DE SEGURIDAD
    out = df.copy()

    state_year = (
        out.groupby(
            ["state_code", "year"],
            observed=True,
            as_index=False)[["SV", "NV", "NS", "LN"]]
        .sum()
    )

    state_year["state_sv_ratio"] = np.where(
        state_year["LN"] > 0,
        state_year["SV"] / state_year["LN"],
        np.nan,
    )

    # ORDENAR POR ESTADO Y AÑO PARA CALCULAR REZAGOS DE MANERA CORRECTA 
    state_year = state_year.sort_values(["state_code", "year"]).reset_index(drop=True)

    state_year["state_sv_ratio_mean_1"] = (
        state_year.groupby("state_code", observed=True)["state_sv_ratio"].shift(1)
    )

    out = out.merge(
        state_year[["state_code", "year", "state_sv_ratio_mean_1"]],
        on=["state_code", "year"],
        how="left",
        validate="m:1",
    )

    out["state_sv_ratio_mean_diff_1"] = (
        out["lag_sv_ratio_1"] - out["state_sv_ratio_mean_1"]
    )

    return out

#----------------------------------
# DEF add_next_targets(): CREA TARGETS DE LA SIGUIENTE ELECCIÓN POR MUNICIPIO.
#---------------------------------- 
def add_next_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea targets de la siguiente elección por municipio.
        Recibe:
            - Dataframe con columnas: CVEGEO, year, sv_ratio, SV.
        Devuelve:
            - Dataframe con columnas adicionales que representan los targets de la siguiente elección por municipio,
              calculados como el valor de sv_ratio y SV para el año siguiente dentro de cada municipio (CVEGEO).
    """
    # VALIDACION
    required_cols = ["CVEGEO", "year", "sv_ratio", "SV",]
    validate_required_columns(df, required_cols, context= "feature_engineering")

    out = df.copy().sort_values(["CVEGEO", "year"]).reset_index(drop=True)

    by = out.groupby("CVEGEO", observed=True)
    out["target_sv_ratio_next"] = by["sv_ratio"].shift(-1)
    out["target_SV_next"] = by["SV"].shift(-1)

    return out

#----------------------------------
# DEF build_modeling_dataframe(): CONSTRUYE EL DATAFRAME FINAL PARA MODELADO INTEGRANDO LAS FUNCIONES ANTERIORES Y ORDENANDO POR MUNICIPIO Y AÑO.
#---------------------------------- 
def build_modeling_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el dataframe final para modelado.
        Recibe:
            - Dataframe con columnas necesarias para construir las características y targets.
        Devuelve:
            - Dataframe final para modelado, que integra las funciones anteriores para construir
              características de composición, rezagos, contexto estatal y targets de la siguiente elección, organizado por municipio (CVEGEO) y año.
    """
    base = build_municipio_year_base(df)
    composition = build_composition_features(df)

    out = base.merge(
        composition,
        on=["state_code", "EDOCVE", "MPIOCVE", "MPIONOM", "year"],
        how="left",
        validate="1:1",
    )

    out = add_lag_features(out)
    out = add_state_context_features(out)
    out = add_next_targets(out)

    return out.sort_values(["CVEGEO", "year"]).reset_index(drop=True)
