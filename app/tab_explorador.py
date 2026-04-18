"""
tab_explorador.py
ARCHIVO ENCARGADO DE LA PESTAÑA PRINCIPAL DEL EXPLORADOR.
"""

# ============================
# IMPORTACIONES
# ============================
from __future__ import annotations

import streamlit as st

from src.base.constants import (
    STATE_LABELS,
    STATE_CODE_FROM_LABEL,
    TIME_SERIES_PALETTE,
)
from src.runtime.charts_altair import (
    build_participation_chart_altair,
    build_state_year_charts_altair,
)
from src.runtime.maps_render import (
    build_national_state_choropleth_plotly,
    build_state_choropleth_plotly,
)
from app.data_access import (
    get_tab_anios_artifact_cached,
    get_tab_estado_artifact_cached,
    get_municipal_geometries_cached,
    get_state_geometries_cached,
)
from app.ui_helpers import render_centered_legend


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def _get_categoria_filename(label: str) -> str:
    mapping = {
        "Sexo": "tab_anios_sexo.parquet",
        "Edad": "tab_anios_edad.parquet",
        "Tipo de sección": "tab_anios_tipo_seccion.parquet",
    }

    if label not in mapping:
        raise ValueError(f"Categoría inválida: {label}")

    return mapping[label]


def _get_estado_categoria_filename(label: str) -> str:
    mapping = {
        "Sexo": "tab_anios_estado_sexo.parquet",
        "Edad": "tab_anios_estado_edad.parquet",
        "Tipo de sección": "tab_anios_estado_tipo_seccion.parquet",
    }

    if label not in mapping:
        raise ValueError(f"Categoría inválida: {label}")

    return mapping[label]


def _render_metricas_izquierda(
    participacion_total: int,
    abstencion_total: int,
) -> None:
    col1, col2, _ = st.columns([1.1, 1.1, 2.2])

    with col1:
        st.metric("Participación total", f"{participacion_total:,}")

    with col2:
        st.metric("Abstención total", f"{abstencion_total:,}")


def _build_bar_view_with_fixed_others(
    df,
    label_col: str,
    top_n: int,
):
    view = df.rename(columns={label_col: "categoria"}).copy()

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
    view = view[cols]

    ordered = view.sort_values("SV", ascending=False).reset_index(drop=True)

    if top_n is None or top_n <= 0 or top_n >= len(ordered):
        category_order = ordered["categoria"].tolist()
        return ordered, category_order

    top = ordered.head(top_n).copy()
    remainder = ordered.iloc[top_n:].copy()

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

    out = ordered.head(top_n).copy()
    out = st.session_state.get("_tmp_df_concat_helper", out) if False else out
    out = __import__("pandas").concat([top, __import__("pandas").DataFrame([others_row])], ignore_index=True)
    category_order = out["categoria"].tolist()

    return out, category_order

#-------------------------------------------------
# HELPER PARA render_tab_explorador()
#-------------------------------------------------
def _render_top_n_stepper(
    label: str,
    session_key: str,
    min_value: int,
    max_value: int,
    default_value: int,
    help_text: str,
) -> int:
    if session_key not in st.session_state:
        st.session_state[session_key] = default_value

    current_value = int(st.session_state[session_key])
    current_value = max(min_value, min(current_value, max_value))
    st.session_state[session_key] = current_value

    st.markdown(f"**{label}**")
    st.caption(help_text)

    col_minus, col_value, col_plus = st.columns([1, 2, 1])

    with col_minus:
        if st.button("−", key=f"{session_key}_minus", use_container_width=True):
            st.session_state[session_key] = max(
                min_value,
                int(st.session_state[session_key]) - 1,
            )

    with col_value:
        st.markdown(
            f"""
            <div style="
                text-align:center;
                font-size:1.1rem;
                font-weight:600;
                padding:0.45rem 0.25rem;
                border:1px solid rgba(128,128,128,0.35);
                border-radius:0.5rem;
                margin-top:0.05rem;
            ">
                {int(st.session_state[session_key])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_plus:
        if st.button("+", key=f"{session_key}_plus", use_container_width=True):
            st.session_state[session_key] = min(
                max_value,
                int(st.session_state[session_key]) + 1,
            )

    return int(st.session_state[session_key])

# -------------------------------------------------
# DEF render_tab_explorador()
# -------------------------------------------------
def render_tab_explorador() -> None:
    modo_explorador = st.selectbox(
        "¿Sobre qué te gustaría conocer más?",
        options=["País", "Estados"],
        index=0,
        key="explorador_modo",
    )

    if modo_explorador == "País":
        _render_explorador_pais()
    else:
        _render_explorador_estados()


# -------------------------------------------------
# DEF _render_explorador_pais()
# -------------------------------------------------
def _render_explorador_pais() -> None:
    df_states_all = get_tab_anios_artifact_cached("tab_anios_estado.parquet")
    df_2024 = df_states_all[df_states_all["year"] == 2024].copy()

    if df_2024.empty:
        st.warning("No hay datos nacionales disponibles para 2024.")
        return

    participacion_total = int(df_2024["SV"].sum())
    abstencion_total = int(df_2024["NV"].sum())

    _render_metricas_izquierda(participacion_total, abstencion_total)

    st.divider()

    col_tabla, col_grafica = st.columns([1, 2], gap="large")

    with col_tabla:
        st.markdown("**Resumen por estado - 2024**")

        table_df = (
            df_2024[["state_label", "SV", "NV"]]
            .rename(
                columns={
                    "state_label": "Estado",
                    "SV": "Participación",
                    "NV": "Abstención",
                }
            )
            .sort_values("Estado", ascending=True)
            .reset_index(drop=True)
        )

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            height=520,
        )

    with col_grafica:
        top_n_estados = _render_top_n_stepper(
            label="Mostrar top de entidades",
            session_key="explorador_pais_top_n_estados",
            min_value=1,
            max_value=32,
            default_value=15,
            help_text="Se muestran las entidades con mayor participación nominal y el resto se agrupa en 'Otros'.",
            )

        view_top, category_order = _build_bar_view_with_fixed_others(
            df_2024,
            label_col="state_label",
            top_n=int(top_n_estados),
        )

        chart = build_participation_chart_altair(
            view_top,
            title="Participación por entidad federativa - 2024",
            category_order=category_order,
        )
        st.altair_chart(chart, use_container_width=True)
        

    st.divider()

    col_mapa, col_series = st.columns([1, 1], gap="large")

    with col_mapa:
        st.markdown("**Mapa nacional por estado**")
        gdf_states = get_state_geometries_cached().copy()
        gdf_map = gdf_states.merge(
            df_2024,
            on=["state_code", "state_label"],
            how="inner",
            validate="1:1",
        )

        fig_map = build_national_state_choropleth_plotly(
            gdf_map=gdf_map,
            column="sv_ratio",
            year=2024,
        )
        st.plotly_chart(fig_map, use_container_width=True)
        st.caption("Escala construida con el porcentaje de participación por entidad federativa.")

    with col_series:
        st.markdown("**Participación a lo largo del tiempo**")

        selected_state_labels = st.multiselect(
            "Selecciona uno o varios estados",
            options=sorted(STATE_LABELS.values()),
            default=["Aguascalientes", "Jalisco", "Nuevo León"],
            help="Ve la tendencia de participación en los estados que quieras.",
            key="explorador_pais_series_estados",
        )

        if len(selected_state_labels) == 0:
            st.info("Selecciona al menos un estado para mostrar la serie temporal.")
        else:
            selected_state_codes = [
                STATE_CODE_FROM_LABEL[label] for label in selected_state_labels
            ]

            series_df = df_states_all[
                df_states_all["state_code"].isin(selected_state_codes)
            ].copy()

            color_domain = [str(code) for code in selected_state_codes]
            color_range = [
                TIME_SERIES_PALETTE[i % len(TIME_SERIES_PALETTE)]
                for i in range(len(color_domain))
            ]

            chart_part, _ = build_state_year_charts_altair(
                series_df,
                title_participacion="Participación por estado a lo largo del tiempo",
                title_abstencion="",
                color_domain=color_domain,
                color_range=color_range,
                series_code_col="state_code",
                series_label_col="state_label",
                series_title="Estado",
            )

            st.altair_chart(chart_part, use_container_width=True)
            render_centered_legend(series_df, color_domain, color_range)
            st.caption("Compara la trayectoria de participación entre una o varias entidades.")

    st.divider()

    categoria = st.selectbox(
        "Participación según categorías",
        options=["Sexo", "Edad", "Tipo de sección"],
        index=0,
        key="explorador_pais_categoria",
    )

    categoria_filename = _get_categoria_filename(categoria)
    categoria_df = get_tab_anios_artifact_cached(categoria_filename).copy()

    color_domain = list(categoria_df["state_code"].astype(str).unique())
    color_range = [
        TIME_SERIES_PALETTE[i % len(TIME_SERIES_PALETTE)]
        for i in range(len(color_domain))
    ]

    chart_part_cat, _ = build_state_year_charts_altair(
        categoria_df,
        title_participacion=f"Participación nacional por {categoria.lower()}",
        title_abstencion="",
        color_domain=color_domain,
        color_range=color_range,
        series_code_col="state_code",
        series_label_col="state_label",
        series_title="Categoría",
    )

    st.altair_chart(chart_part_cat, use_container_width=True)
    render_centered_legend(categoria_df, color_domain, color_range)
    st.caption("Explora cómo cambia la participación a lo largo del tiempo según la categoría seleccionada.")


# -------------------------------------------------
# DEF _render_explorador_estados()
# -------------------------------------------------
def _render_explorador_estados() -> None:
    state_label = st.selectbox(
        "¿Sobre qué estado te gustaría conocer?",
        options=sorted(STATE_LABELS.values()),
        index=0,
        key="explorador_estado_seleccionado",
    )
    state_code = STATE_CODE_FROM_LABEL[state_label]

    df_municipios_all = get_tab_estado_artifact_cached("tab_estado_municipio.parquet")
    df_state_2024 = df_municipios_all[
        (df_municipios_all["state_code"] == state_code)
        & (df_municipios_all["year"] == 2024)
    ].copy()

    if df_state_2024.empty:
        st.warning("No hay datos municipales disponibles para el estado seleccionado.")
        return

    participacion_total = int(df_state_2024["SV"].sum())
    abstencion_total = int(df_state_2024["NV"].sum())

    _render_metricas_izquierda(participacion_total, abstencion_total)

    st.divider()

    col_tabla, col_grafica = st.columns([1, 2], gap="large")

    with col_tabla:
        st.markdown("**Resumen por municipio - 2024**")

        table_df = (
            df_state_2024[["categoria", "SV", "NV"]]
            .rename(
                columns={
                    "categoria": "Municipio",
                    "SV": "Participación",
                    "NV": "Abstención",
                }
            )
            .sort_values("Municipio", ascending=True)
            .reset_index(drop=True)
        )

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            height=520,
        )

    with col_grafica:
        top_n_municipios = _render_top_n_stepper(
    label="Mostrar top de municipios",
    session_key=f"explorador_estado_top_n_municipios_{state_code}",
    min_value=1,
    max_value=min(600, len(df_state_2024)),
    default_value=min(15, len(df_state_2024)),
    help_text="El resto de los municipios se agrupa como 'Otros'.",
)

        view_top, category_order = _build_bar_view_with_fixed_others(
            df_state_2024,
            label_col="categoria",
            top_n=int(top_n_municipios),
        )

        chart = build_participation_chart_altair(
            view_top,
            title=f"Participación por municipio en {state_label} - 2024",
            category_order=category_order,
        )
        st.altair_chart(chart, use_container_width=True)

    st.divider()

    col_mapa, col_series = st.columns([1, 1], gap="large")

    with col_mapa:
        st.markdown("**Mapa municipal del estado**")

        df_map_all = get_tab_estado_artifact_cached("tab_estado_mapa.parquet")
        df_map = df_map_all[
            (df_map_all["state_code"] == state_code)
            & (df_map_all["year"] == 2024)
        ].copy()

        gdf_municipios = get_municipal_geometries_cached()
        gdf_map = gdf_municipios.merge(
            df_map,
            on="CVEGEO",
            how="inner",
            validate="1:1",
        )

        fig_map = build_state_choropleth_plotly(
            gdf_map=gdf_map,
            column="sv_ratio",
            state_name=state_label,
            year=2024,
        )
        st.plotly_chart(fig_map, use_container_width=True)
        st.caption("Escala construida con el porcentaje de participación por municipio.")

    with col_series:
        st.markdown("**Participación municipal a lo largo del tiempo**")

        selected_municipios = st.multiselect(
            "Selecciona uno o varios municipios",
            options=sorted(df_state_2024["categoria"].astype(str).unique()),
            default=sorted(df_state_2024["categoria"].astype(str).unique())[:3],
            help="Compara la trayectoria de participación entre municipios del estado seleccionado.",
            key="explorador_estado_series_municipios",
        )

        if len(selected_municipios) == 0:
            st.info("Selecciona al menos un municipio para mostrar la serie temporal.")
        else:
            series_df = df_municipios_all[
                (df_municipios_all["state_code"] == state_code)
                & (df_municipios_all["categoria"].isin(selected_municipios))
            ].copy()

            plot_series_df = series_df.copy()
            plot_series_df["state_code"] = series_df["categoria"].astype(str)
            plot_series_df["state_label"] = series_df["categoria"].astype(str)

            color_domain = list(plot_series_df["state_code"].astype(str).unique())
            color_range = [
                TIME_SERIES_PALETTE[i % len(TIME_SERIES_PALETTE)]
                for i in range(len(color_domain))
            ]

            chart_part, _ = build_state_year_charts_altair(
                plot_series_df,
                title_participacion=f"Participación municipal en {state_label}",
                title_abstencion="",
                color_domain=color_domain,
                color_range=color_range,
                series_code_col="state_code",
                series_label_col="state_label",
                series_title="Municipio",
            )

            st.altair_chart(chart_part, use_container_width=True)
            render_centered_legend(plot_series_df, color_domain, color_range)
            st.caption("Compara la evolución de participación entre municipios del estado.")

    st.divider()

    categoria = st.selectbox(
        "Participación según categorías",
        options=["Sexo", "Edad", "Tipo de sección"],
        index=0,
        key="explorador_estado_categoria",
    )

    categoria_filename = _get_estado_categoria_filename(categoria)
    categoria_df_all = get_tab_anios_artifact_cached(categoria_filename)
    categoria_df = categoria_df_all[
        categoria_df_all["state_code"] == state_code
    ].copy()

    if categoria_df.empty:
        st.info("No hay datos por categoría para el estado seleccionado.")
        return

    plot_categoria_df = categoria_df.copy()

    color_domain = list(plot_categoria_df["serie_code"].astype(str).unique())
    color_range = [
        TIME_SERIES_PALETTE[i % len(TIME_SERIES_PALETTE)]
        for i in range(len(color_domain))
    ]

    chart_part_cat, _ = build_state_year_charts_altair(
        plot_categoria_df,
        title_participacion=f"Participación en {state_label} por {categoria.lower()}",
        title_abstencion="",
        color_domain=color_domain,
        color_range=color_range,
        series_code_col="serie_code",
        series_label_col="serie_label",
        series_title="Categoría",
    )

    legend_df = plot_categoria_df[["serie_code", "serie_label"]].drop_duplicates().rename(
        columns={
            "serie_code": "state_code",
            "serie_label": "state_label",
        }
    )

    st.altair_chart(chart_part_cat, use_container_width=True)
    render_centered_legend(legend_df, color_domain, color_range)
    st.caption("Explora cómo cambia la participación en el estado según la categoría seleccionada.")