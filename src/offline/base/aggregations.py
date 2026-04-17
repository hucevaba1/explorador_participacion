"""
aggregations.py
# ARCHIVO DE AGRUPACIONES PARA EL PROYECTO DE ANÁLISIS DE DATOS ELECTORALES:
Este módulo se encarga de:
- calcular ratios de participación,
- agrupar por una dimensión específica,
- agrupar por dimensión + año,
- agrupar por estado + año.

Cada función devuelve un DataFrame con las sumas de SV, NV, NS y LN,
así como los ratios correspondientes.
"""

# --------------------------------
# IMPORTACIONES
# --------------------------------  
from __future__ import annotations

import numpy as np
import pandas as pd

from src.base.validator import validate_required_columns

# =====================================================
# DEF _compute_ratios(): AÑADE COLUMNAS DE RATIOS:
# sv_ratio = SV / LN
# nv_ratio = NV / LN
# ns_ratio = NS / LN
# =====================================================
def _compute_ratios(
    df: pd.DataFrame,
    sv_col: str = "SV",
    nv_col: str = "NV",
    ns_col: str = "NS",
    ln_col: str = "LN",
) -> pd.DataFrame:
    """
    Añade columnas de ratios al DataFrame:
        - total_marked: SV + NV
        - sv_ratio: SV / LN
        - nv_ratio: NV / LN
        - ns_ratio: NS / LN (si existe la columna NS; en otro caso, NaN)
    """
    out = df.copy()

    validate_required_columns(out, 
                              [sv_col, nv_col, ln_col],
                              context="aggregations._compute_ratios",
                              )

    out["total_marked"] = out[sv_col] + out[nv_col]

    valid_ln = out[ln_col] > 0

    out["sv_ratio"] = np.where(valid_ln, out[sv_col] / out[ln_col], np.nan)
    out["nv_ratio"] = np.where(valid_ln, out[nv_col] / out[ln_col], np.nan)

    if ns_col in out.columns:
        out["ns_ratio"] = np.where(valid_ln, out[ns_col] / out[ln_col], np.nan)
    else:
        out["ns_ratio"] = np.nan

    return out

# =====================================================
# DEF _aggregate_sum_and_compute_ratios(): UTILIDAD INTERNA PARA AGRUPAR, SUMAR, Y CALCULAR RATIOS DE INTERÉS
# =====================================================
def _aggregate_sum_and_compute_ratios(
    df: pd.DataFrame,
    group_cols: list[str],
    sv_col: str = "SV",
    nv_col: str = "NV",
    ns_col: str = "NS",
    ln_col: str = "LN",
    reset_index: bool = False,
) -> pd.DataFrame:
    """
    Agrupa por una dimensión específica, suma SV, NV, NS y LN,
    calcula ratios y ordena por sv_ratio de mayor a menor.
    """
    required_cols = group_cols + [sv_col, nv_col, ns_col, ln_col]

    validate_required_columns(
        df,
        required_cols,
        context="aggregations._aggregate_sum_and_compute_ratios")

    value_cols = [sv_col, nv_col, ns_col, ln_col]

    out = (
        df.groupby(group_cols, observed=True)[value_cols]
        .sum(min_count=1)
    )

    if reset_index:
        out = out.reset_index()

    for col in value_cols:
        out[col] = out[col].fillna(0).astype("int32")

    out = _compute_ratios(
        out,
        sv_col=sv_col,
        nv_col=nv_col,
        ns_col=ns_col,
        ln_col=ln_col,
    )

    return out

# =====================================================
# DEF aggregate_group():
# =====================================================
def aggregate_group(
    df: pd.DataFrame,
    group_col: str,
    sv_col: str = "SV",
    nv_col: str = "NV",
    ns_col: str = "NS",
    ln_col: str = "LN",
) -> pd.DataFrame:
    """
    Agrupa por una dimensión específica, suma SV, NV, NS y LN,
    calcula ratios y ordena por sv_ratio de mayor a menor.
    """
    out = _aggregate_sum_and_compute_ratios(
        df,
        group_cols=[group_col],
        sv_col=sv_col,
        nv_col=nv_col,
        ns_col=ns_col,
        ln_col=ln_col,
        reset_index=False,
    )

    return out.sort_values("sv_ratio", ascending=False)

# =====================================================
# DEF aggregate_group_year():
# =====================================================
def aggregate_group_year(
    df: pd.DataFrame,
    group_col: str,
    year_col: str = "year",
    sv_col: str = "SV",
    nv_col: str = "NV",
    ns_col: str = "NS",
    ln_col: str = "LN",
) -> pd.DataFrame:
    """
    Agrupa por dimensión + año, suma SV, NV, NS y LN,
    calcula ratios y ordena por dimensión y año.
    """
    out = _aggregate_sum_and_compute_ratios(
        df,
        group_cols=[group_col, year_col],
        sv_col=sv_col,
        nv_col=nv_col,
        ns_col=ns_col,
        ln_col=ln_col,
        reset_index=True,
    )

    return out.sort_values([group_col, year_col]).reset_index(drop=True)

# =====================================================
# DEF aggregate_state_year():
# =====================================================
def aggregate_state_year(
    df: pd.DataFrame,
    sv_col: str = "SV",
    nv_col: str = "NV",
    ns_col: str = "NS",
    ln_col: str = "LN",
) -> pd.DataFrame:
    """
    Agrupa por estado + año, suma SV, NV, NS y LN,
    calcula ratios y ordena por estado y año.
    """
    out = _aggregate_sum_and_compute_ratios(
        df,
        group_cols=["state_code", "year"],
        sv_col=sv_col,
        nv_col=nv_col,
        ns_col=ns_col,
        ln_col=ln_col,
        reset_index=True,
    )

    return out.sort_values(["state_code", "year"]).reset_index(drop=True)
