"""
ui_helpers.py
ARCHIVO ENCARGADO DE LAS FUNCIONES AUXILIARES DE LA INTERFAZ Y MÉTRCIAS DE PRESENTACIÓN PARA LA APLICACIÓN EN STREAMLIT.
"""

#============================
# IMPORTACIONES
#============================
from __future__ import annotations

import streamlit as st
import pandas as pd 

# -------------------------------------------------
# HELPERS MÉTRICAS
# -------------------------------------------------
def compute_weighted_metrics(df: pd.DataFrame) -> tuple[float, float]:
    sv_total = int(df["SV"].sum()) if "SV" in df.columns else 0
    nv_total = int(df["NV"].sum()) if "NV" in df.columns else 0
    ln_total = int(df["LN"].sum()) if "LN" in df.columns else 0

    if ln_total == 0:
        return 0.0, 0.0

    return sv_total / ln_total, nv_total / ln_total

# -------------------------------------------------
# HELPERS UI
# -------------------------------------------------
def render_centered_legend(
    df: pd.DataFrame,
    color_domain: list[str],
    color_range: list[str],
) -> None:
    if len(color_domain) != len(color_range):
        raise ValueError(
            "color_domain y color_range deben tener la misma longitud."
        )

    label_map = (
        df[["state_code", "state_label"]]
        .drop_duplicates()
        .assign(state_code=lambda d: d["state_code"].astype(str))
        .set_index("state_code")["state_label"]
        .to_dict()
    )

    legend_items = []
    for i, code in enumerate(color_domain):
        label = label_map.get(str(code), str(code))
        color = color_range[i]

        legend_items.append(
            f'<span style="display:inline-flex; align-items:center; margin:0 12px 8px 12px; font-size:0.95rem;">'
            f'<span style="width:12px; height:12px; border-radius:50%; background:{color}; display:inline-block; margin-right:6px;"></span>'
            f"{label}"
            f"</span>"
        )

    legend_html = (
        '<div style="text-align:center; margin-top:18px; margin-bottom:4px; line-height:1.8;">'
        + "".join(legend_items)
        + "</div>"
    )

    st.markdown(legend_html, unsafe_allow_html=True)


def render_time_series_metrics(
    df: pd.DataFrame,
    series_col: str = "state_code",
) -> None:
    participacion, sin_marca = compute_weighted_metrics(df)

    if series_col not in df.columns:
        raise ValueError(
            f"La columna de series {series_col!r} no existe en el DataFrame."
        )

    if "year" not in df.columns:
        raise ValueError("La columna 'year' no existe en el DataFrame.")

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)

    with col_meta1:
        st.metric("Series totales", int(df[series_col].nunique()))

    with col_meta2:
        st.metric("Años", int(df["year"].nunique()))

    with col_meta3:
        st.metric("Participación ponderada", f"{participacion:.1%}")

    with col_meta4:
        st.metric("Abstencionismo ponderado", f"{sin_marca:.1%}")