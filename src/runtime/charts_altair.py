"""
charts_altair.py
Funciones de gráficos Altair para la capa runtime de la app.
"""

# ============================
# IMPORTACIONES
# ============================
from __future__ import annotations

import altair as alt
import pandas as pd

from src.base.constants import STATE_LABELS


# =====================================================
# DEF build_participation_chart_altair()
# =====================================================
def build_participation_chart_altair(
    view: pd.DataFrame,
    title: str | None = None,
    category_order: list[str] | None = None,
) -> alt.Chart:
    """
    Devuelve un gráfico de Altair a partir del view para la pestaña Por estado.
    """
    sv_total_all = int(view["SV"].sum()) if "SV" in view.columns else 0
    nv_total_all = int(view["NV"].sum()) if "NV" in view.columns else 0
    ns_total_all = int(view["NS"].sum()) if "NS" in view.columns else 0
    ln_total_all = int(view["LN"].sum()) if "LN" in view.columns else 0

    sv_total_pct = (sv_total_all / ln_total_all * 100) if ln_total_all > 0 else None
    nv_total_pct = (nv_total_all / ln_total_all * 100) if ln_total_all > 0 else None
    ns_total_pct = (ns_total_all / ln_total_all * 100) if ln_total_all > 0 else None

    df_plot = view.copy()
    df_plot["sv_pct"] = (df_plot["sv_ratio"] * 100).fillna(0)
    df_plot["nv_pct"] = (df_plot["nv_ratio"] * 100).fillna(0)
    df_plot["ns_pct"] = (df_plot["ns_ratio"] * 100).fillna(0)

    if title is None:
        title = "% Participación sobre lista nominal"

    subtitle_lines = []
    if ln_total_all > 0:
        subtitle_lines.append(
            f"SV: {sv_total_all:,} ({sv_total_pct:.1f}%)  |  "
            f"NV: {nv_total_all:,} ({nv_total_pct:.1f}%)  |  "
            f"NS: {ns_total_all:,} ({ns_total_pct:.1f}%)"
        )

    title_param = alt.TitleParams(text=title, subtitle=subtitle_lines)

    long = df_plot.melt(
        id_vars=["categoria", "SV", "NV", "NS"],
        value_vars=["sv_pct", "nv_pct", "ns_pct"],
        var_name="serie_raw",
        value_name="pct",
    )

    long["serie"] = long["serie_raw"].map(
        {
            "sv_pct": "Participación",
            "nv_pct": "Abstencionismo",
            "ns_pct": "Registros inválidos",
        }
    )

    long["total_serie"] = 0
    long.loc[long["serie_raw"] == "sv_pct", "total_serie"] = long.loc[
        long["serie_raw"] == "sv_pct", "SV"
    ]
    long.loc[long["serie_raw"] == "nv_pct", "total_serie"] = long.loc[
        long["serie_raw"] == "nv_pct", "NV"
    ]
    long.loc[long["serie_raw"] == "ns_pct", "total_serie"] = long.loc[
        long["serie_raw"] == "ns_pct", "NS"
    ]

    long["serie_order"] = long["serie"].map(
        {"Participación": 0, "Abstencionismo": 1, "Registros inválidos": 2}
    ).astype("int8")

    chart = (
        alt.Chart(long, title=title_param)
        .mark_bar()
        .encode(
            y=alt.Y(
                "categoria:N",
                sort=category_order if category_order is not None else alt.SortField(field="SV", order="descending"),
                title=None,
                ),
            x=alt.X(
                "pct:Q",
                stack="zero",
                title="% sobre lista nominal",
            ),
            color=alt.Color(
                "serie:N",
                title=None,
                sort=["Participación", "Abstencionismo", "Registros inválidos"],
                scale=alt.Scale(
                    domain=["Participación", "Abstencionismo", "Registros inválidos"],
                    range=["#8fbc8f", "#CD5C5C", "#9E9E9E"],
                ),
                legend=alt.Legend(orient="bottom"),
            ),
            order=alt.Order("serie_order:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("categoria:N", title="Categoría"),
                alt.Tooltip("serie:N", title="Serie"),
                alt.Tooltip("pct:Q", title="%", format=".1f"),
                alt.Tooltip("total_serie:Q", title="Total", format=","),
            ],
        )
        .interactive()
        .properties(height=420)
    )

    return chart


# =====================================================
# DEF build_state_year_charts_altair()
# =====================================================
def build_state_year_charts_altair(
    state_year_view: pd.DataFrame,
    title_participacion: str = "Participación por estado",
    title_abstencion: str = "Abstencionismo por estado",
    color_domain: list[str] | None = None,
    color_range: list[str] | None = None,
    series_code_col: str = "state_code",
    series_label_col: str = "state_label",
    series_title: str = "Serie",
) -> tuple[alt.Chart, alt.Chart]:
    """
    Devuelve dos charts de Altair para series temporales por grupo.
    """
    df = state_year_view.copy()

    if series_label_col not in df.columns and series_code_col in df.columns:
        if series_code_col == "state_code":
            df[series_label_col] = df[series_code_col].map(STATE_LABELS).fillna(
                df[series_code_col].astype(str)
            )
        else:
            df[series_label_col] = df[series_code_col].astype(str)

    color_enc = alt.Color(
        f"{series_code_col}:N",
        title=None,
        legend=None,
        scale=alt.Scale(domain=color_domain, range=color_range)
        if (color_domain and color_range)
        else alt.Undefined,
    )

    base = alt.Chart(df).encode(
        x=alt.X("year:O", title="Año"),
        color=color_enc,
    )

    chart_participacion = (
        base.properties(title=alt.TitleParams(text=title_participacion))
        .mark_line(point=True)
        .encode(
            y=alt.Y(
                "sv_ratio:Q",
                title="%",
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%"),
            ),
            tooltip=[
                alt.Tooltip(f"{series_label_col}:N", title=series_title),
                alt.Tooltip("year:O", title="Año"),
                alt.Tooltip("sv_ratio:Q", title="% Participación", format=".2%"),
                alt.Tooltip("SV:Q", title="Participación nominal", format=","),
                alt.Tooltip("nv_ratio:Q", title="% Abstención", format=".2%"),
                alt.Tooltip("NV:Q", title="Abstención nominal", format=","),
            ],
        )
        .interactive()
        .properties(height=320)
    )

    chart_abstencion = (
        base.properties(title=alt.TitleParams(text=title_abstencion))
        .mark_line(point=True)
        .encode(
            y=alt.Y(
                "nv_ratio:Q",
                title="%",
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%"),
            ),
            tooltip=[
                alt.Tooltip(f"{series_label_col}:N", title=series_title),
                alt.Tooltip("year:O", title="Año"),
                alt.Tooltip("sv_ratio:Q", title="% Participación", format=".2%"),
                alt.Tooltip("SV:Q", title="Participación nominal", format=","),
                alt.Tooltip("nv_ratio:Q", title="% Abstención", format=".2%"),
                alt.Tooltip("NV:Q", title="Abstención nominal", format=","),
            ],
        )
        .interactive()
        .properties(height=320)
    )

    return chart_participacion, chart_abstencion