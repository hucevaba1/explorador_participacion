"""
view_models.py
ARCHIVO ENCARGADO DE LOS MODELOS DE VISTA PARA LAS PESTAÑAS DE ESTADO y AÑOS
Este módulo contiene funciones que preparan los datos para las vistas de las pestañas de estado y años.
"""

# --------------------------------
# IMPORTACIONES
# --------------------------------
from __future__ import annotations
import pandas as pd

from src.base.constants import (
    STATE_LABELS,
    GROUPINGS,
)
from src.base.aggregations import (
    aggregate_group,
    aggregate_group_year,
    aggregate_state_year
)

# =====================================================
# DEF get_view(): DEVUELVE UN VIEW MODEL PARA LA PESTAÑA POR ESTADO
# =====================================================
def get_view(
    df: pd.DataFrame,
    grouping_label: str,
) -> pd.DataFrame:
    """
    Devuelve un view model para la pestaña Por estado.
    Recibe:
    - df: DataFrame con los datos electorales
    - grouping_label: etiqueta de agrupación (estado, municipio, distrito, sección)
    Devuelve:
    - DataFrame con las columnas:
        - categoria: nombre de la categoría agrupada (estado, municipio, distrito, sección)
        - SV: suma de votos válidos
        - NV: suma de votos nulos
        - NS: suma de votos no registrados (si existe la columna NS, si no se llena con NaN)
        - LN: suma de lista nominal
        - total_marked: suma de SV + NV
        - sv_ratio: ratio de SV sobre LN
        - nv_ratio: ratio de NV sobre LN
        - ns_ratio: ratio de NS sobre LN
    """
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

# =====================================================
# DEF limit_categories(): LIMITA EL NÚMERO DE CATEGORÍAS EN EL VIEW MODEL PARA LA PESTAÑA POR ESTADO 
# =====================================================
def limit_categories(
    view: pd.DataFrame,
    top_n: int | None,
    by: str = "SV",
    others: bool = True,
) -> pd.DataFrame:
    """
    Limita el número de categorías en el view model para la pestaña Por estado.
    Recibe:
        - view: DataFrame con el view model completo 
        - top_n: número de categorías a mostrar (si es None o <= 0, no se limita)
        - by: columna por la cual ordenar. SV por defecto.
        - others: si incluir la categoría "Otros" con la suma de las categorías restantes. True por defecto.
    Devuelve:
        - DataFrame con las categorías limitadas
    """
    if top_n is None or top_n <= 0:
        return view

    if by not in view.columns:
        raise ValueError(f"Columna inválida para ordenar: {by}")

    ordered = view.sort_values(by, ascending=False)

    top = ordered.head(top_n)
    remainder = ordered.iloc[top_n:]

    if remainder.empty or not others:
        return top

    sv_sum = remainder["SV"].sum()
    nv_sum = remainder["NV"].sum()
    ns_sum = remainder["NS"].sum()
    ln_sum = remainder["LN"].sum()
    total_marked_sum = remainder["total_marked"].sum()

    others_row = {
        "categoria": "Otros",
        "SV": sv_sum,
        "NV": nv_sum,
        "NS": ns_sum,
        "LN": ln_sum,
        "total_marked": total_marked_sum,
        "sv_ratio": sv_sum / ln_sum if ln_sum > 0 else 0,
        "nv_ratio": nv_sum / ln_sum if ln_sum > 0 else 0,
        "ns_ratio": ns_sum / ln_sum if ln_sum > 0 else 0,
    }

    others_df = pd.DataFrame([others_row])

    return pd.concat([top, others_df], ignore_index=True)

# ===================================================== 
# DEF get_participation_view_for_chart(): DEVUELVE UN VIEW MODEL PARA LA PESTAÑA POR ESTADO CON LAS COLUMNAS DE RATIOS CALCULADAS Y LIMITADO A TOP_N CATEGORÍAS SI SE ESPECIFICA
# ===================================================== 
def get_participation_view_for_chart(
    df: pd.DataFrame,
    grouping_label: str,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Devuelve un view model para la pestaña Por estado con las columnas de ratios calculadas y limitado a top_n categorías si se especifica. 
    Recibe:
        - df: DataFrame con los datos electorales
        - grouping_label: etiqueta de agrupación (estado, municipio, distrito, sección)
        - top_n: número de categorías a mostrar (si es None o <= 0, no se limita)
    Devuelve:
        - DataFrame aplicando:
            - get_view() para obtener el view model completo
            - limit_categories() para limitar el número de categorías si se especifica
    """
    view = get_view(df, grouping_label=grouping_label)

    if grouping_label == "Mostrar por municipio":
        view = limit_categories(view, top_n=top_n, by="SV", others=True)

    return view

# =====================================================
# DEF get_group_year_view(): DEVUELVE UN VIEW MODEL PARA SERIES DE TIEMPO POR GRUPO Y POR ESTADO
# ===================================================== 
def get_group_year_view(
    df: pd.DataFrame,
    group_col: str,
) -> pd.DataFrame:
    """
    Devuelve un view model para series de tiempo por grupo y por estado.
        Recibe:
            - df: DataFrame con los datos electorales
            - group_col: nombre de la columna de agrupación (state_code, municipality_code, district_code, section_code)
        Devuelve:
            - DataFrame agrupado por estado y año, con las sumas de SV, NV, NS y LN y las columnas de ratios calculadas y ordenadas por estado y año
    """
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

# =====================================================
# DEF get_state_year_view(): DEVUELVE UN VIEW MODEL PARA SERIES DE TIEMPO POR ESTADO
# =====================================================
def get_state_year_view(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve un view model para series de tiempo por estado.
    Recibe:
        - df: DataFrame con los datos electorales
    Devuelve:
        - DataFrame agrupado por estado y año, con las sumas de SV, NV, NS y LN y las columnas de ratios calculadas y ordenadas por estado y año 
    """
    return get_group_year_view(df, group_col="state_code")