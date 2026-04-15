"""
tab_anios.py
ARCHIVO ENCARGADO DE LA PESTAÑA DE ANÁLISIS POR AÑOS
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
from src.views import build_state_year_charts_altair
from app.ui_helpers import (
    render_centered_legend,
    render_time_series_metrics,
)
from app.data_access import get_tab_anios_artifact_cached


# ============================
# ADECUACIÓN A NOMBRE DE OBJETO PARA CARGA DESDE data_access
# ============================
def _get_tab_anios_filename(mode: str) -> str:
    mapping = {
        "estado": "tab_anios_estado.parquet",
        "sexo": "tab_anios_sexo.parquet",
        "edad": "tab_anios_edad.parquet",
        "tipo_seccion": "tab_anios_tipo_seccion.parquet",
    }

    if mode not in mapping:
        raise ValueError(f"Modo inválido para tab_años: {mode}")

    return mapping[mode]


def _get_dimension_key_from_label(label: str) -> str:
    mapping = {
        "Sexo": "sexo",
        "Edad": "edad",
        "Tipo de sección": "tipo_seccion",
    }

    if label not in mapping:
        raise ValueError(f"Dimensión inválida: {label}")

    return mapping[label]


def _get_tab_anios_state_dimension_filename(label: str) -> str:
    mapping = {
        "Sexo": "tab_anios_estado_sexo.parquet",
        "Edad": "tab_anios_estado_edad.parquet",
        "Tipo de sección": "tab_anios_estado_tipo_seccion.parquet",
    }

    if label not in mapping:
        raise ValueError(f"Dimensión inválida: {label}")

    return mapping[label]


# -------------------------------------------------
# DEF render_tab_anios(): Gestiona los elementos del TAB
# -------------------------------------------------
def render_tab_anios() -> None:
    st.caption(
        "Observa la participación y el abstencionismo por categoría a lo largo del tiempo a nivel nacional o estatal."
    )

    st.subheader("Análisis nacional")

    col_controls_nacional, col_results_nacional = st.columns([1, 3], gap="large")

    with col_controls_nacional:
        with st.container(border=True):
            st.subheader("Filtrar por")

            national_mode = st.selectbox(
                "Modo de análisis",
                options=["Ver país", "Comparación entre estados"],
                index=0,
                help="Elige entre datos agregados a nivel nacional o la comparación entre estados.",
                key="tab_anios_national_mode",
            )

            selected_state_labels: list[str] = []

            if national_mode == "Ver país":
                national_dimension = st.selectbox(
                    "Categoría:",
                    options=["Sexo", "Edad", "Tipo de sección"],
                    index=0,
                    key="tab_anios_national_dimension",
                )
            else:
                selected_state_labels = st.multiselect(
                    "Selecciona los estados",
                    options=sorted(STATE_LABELS.values()),
                    default=["Aguascalientes"],
                    help="Selecciona uno o varios estados para comparar sus trayectorias.",
                    key="tab_anios_states",
                )

    with col_results_nacional:
        with st.status("Preparando análisis nacional...", expanded=False) as status:
            if national_mode == "Ver país":
                dimension_key = _get_dimension_key_from_label(national_dimension)
                filename = _get_tab_anios_filename(dimension_key)

                time_view = get_tab_anios_artifact_cached(filename).copy()
                status.write("Artefacto nacional cargado")

                color_domain = list(time_view["state_code"].astype(str).unique())

            else:
                if len(selected_state_labels) == 0:
                    st.info("Selecciona al menos un estado para mostrar la gráfica.")
                    return

                selected_state_codes = [
                    STATE_CODE_FROM_LABEL[label] for label in selected_state_labels
                ]

                time_view = get_tab_anios_artifact_cached("tab_anios_estado.parquet")
                time_view = time_view[
                    time_view["state_code"].isin(selected_state_codes)
                ].copy()

                status.write("Artefacto por estado cargado")
                status.write("Filtro por estados aplicado")

                color_domain = [str(code) for code in selected_state_codes]

            if time_view.empty:
                status.update(label="Sin datos disponibles", state="error")
                st.warning("No hay datos disponibles para la selección actual.")
                return

            color_range = [
                TIME_SERIES_PALETTE[i % len(TIME_SERIES_PALETTE)]
                for i in range(len(color_domain))
            ]

            status.update(label="Análisis nacional listo", state="complete")

        with st.spinner("Renderizando gráficas..."):
            if national_mode == "Ver país":
                title_part = f"Participación nacional por {national_dimension.lower()}"
                title_nv = (
                    f"Abstencionismo nacional por "
                    f"{national_dimension.lower()}"
                )
            else:
                title_part = "Participación por estado"
                title_nv = "Abstencionismo por estado"

            c1, c2 = build_state_year_charts_altair(
                time_view,
                title_participacion=title_part,
                title_abstencion=title_nv,
                color_domain=color_domain,
                color_range=color_range,
            )

        render_time_series_metrics(time_view)

        st.divider()

        col_part, col_nv = st.columns(2, gap="large")

        with col_part:
            st.subheader("Participación")
            st.altair_chart(c1, use_container_width=True)

        with col_nv:
            st.subheader("Abstencionismo")
            st.altair_chart(c2, use_container_width=True)

        render_centered_legend(time_view, color_domain, color_range)

    st.divider()

    st.subheader("Análisis estatal")

    col_controls_state, col_results_state = st.columns([1, 4], gap="large")

    with col_controls_state:
        with st.container(border=True):
            st.subheader("Filtrar por")

            state_label = st.selectbox(
                "Selecciona un estado",
                options=sorted(STATE_LABELS.values()),
                key="tab_anios_state_section_state",
            )

            state_dimension = st.selectbox(
                "Categoría:",
                options=["Sexo", "Edad", "Tipo de sección"],
                key="tab_anios_state_section_dimension",
            )

            state_code = STATE_CODE_FROM_LABEL[state_label]

    with col_results_state:
        with st.status("Preparando análisis por estado...", expanded=False) as status:
            filename = _get_tab_anios_state_dimension_filename(state_dimension)

            time_view_state = get_tab_anios_artifact_cached(filename)
            time_view_state = time_view_state[
                time_view_state["state_code"] == state_code
            ].copy()

            status.write("Artefacto estatal por dimensión cargado")
            status.write("Filtro por estado aplicado")

            if time_view_state.empty:
                status.update(label="Sin datos disponibles", state="error")
                st.warning("No hay datos disponibles para el estado seleccionado.")
                return

            plot_view_state = time_view_state[["serie_code", "serie_label","year", "SV",
                                               "NV", "NS", "LN", "total_marked", "sv_ratio",
                                               "nv_ratio", "ns_ratio",]].rename(
                                                   columns={
                                                       "serie_code": "state_code",
                                                       "serie_label": "state_label",}
                                                       ).copy()

            color_domain = list(plot_view_state["state_code"].astype(str).unique())
            color_range = [
                TIME_SERIES_PALETTE[i % len(TIME_SERIES_PALETTE)]
                for i in range(len(color_domain))
            ]

            status.update(label="Análisis por estado listo", state="complete")

        with st.spinner("Renderizando gráficas..."):
            title_part = (
                f"Participación en {state_label} por {state_dimension.lower()}"
            )
            title_nv = (
                f"Abstencionismo en {state_label} por {state_dimension.lower()}"
            )

            c1_state, c2_state = build_state_year_charts_altair(
                plot_view_state,
                title_participacion=title_part,
                title_abstencion=title_nv,
                color_domain=color_domain,
                color_range=color_range,
            )

        render_time_series_metrics(plot_view_state, series_col="state_code")

        st.divider()

        col_part, col_nv = st.columns(2, gap="large")

        with col_part:
            st.subheader("Participación")
            st.altair_chart(c1_state, use_container_width=True)

        with col_nv:
            st.subheader("Abstencionismo")
            st.altair_chart(c2_state, use_container_width=True)

        render_centered_legend(plot_view_state, color_domain, color_range)