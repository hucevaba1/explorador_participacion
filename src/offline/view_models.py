"""
view_models.py
Funciones de construcción de vistas agregadas para la capa offline.
"""
#=======================================
# IMPORTACIONES
#=======================================
from __future__ import annotations

import pandas as pd

from src.offline.base.aggregations import (
    aggregate_group,
    aggregate_group_year,
    aggregate_state_year,
)
from src.base.constants import (
    GROUPINGS,
    STATE_LABELS,
)

#=======================================
# FUNCIONES
#=======================================
def get_view(
    df: pd.DataFrame,
    grouping_label: str,
) -> pd.DataFrame:
    group_col = GROUPINGS.get(grouping_label)

    if group_col is None:
        raise ValueError(
            f"Grouping inválido: {grouping_label}. Opciones: {list(GROUPINGS.keys())}"
        )

    agg = aggregate_group(df, group_col)

    out = agg.reset_index().rename(columns={group_col: "categoria"})
    out["categoria"] = out["categoria"].astype("string")

    cols = [
        "categoria",
        "SV",
        "NV",
        "NS",
        "LN",
        "total_marked",
        "sv_ratio",
        "nv_ratio",
        "ns_ratio",
    ]

    return out[cols]


def get_group_year_view(
    df: pd.DataFrame,
    group_col: str,
) -> pd.DataFrame:
    if group_col == "state_code":
        out = aggregate_state_year(df)
        out["state_label"] = out["state_code"].map(STATE_LABELS).fillna(
            out["state_code"].astype(str)
        )
    else:
        out = aggregate_group_year(df, group_col=group_col)
        out = out.rename(columns={group_col: "state_code"})
        out["state_label"] = out["state_code"].astype(str)

    out["state_code"] = out["state_code"].astype("string")
    out["year"] = out["year"].astype("int16")

    cols = [
        "state_code",
        "state_label",
        "year",
        "SV",
        "NV",
        "NS",
        "LN",
        "total_marked",
        "sv_ratio",
        "nv_ratio",
        "ns_ratio",
    ]

    return out[cols].sort_values(["state_code", "year"]).reset_index(drop=True)


def get_state_year_view(df: pd.DataFrame) -> pd.DataFrame:
    return get_group_year_view(df, group_col="state_code")