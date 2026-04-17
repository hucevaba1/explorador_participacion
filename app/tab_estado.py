"""
tab_estado.py
ARCHIVO ENCARGADO DE LA PESTAÑA DE ANÁLISIS POR ESTADO
"""
#============================
# IMPORTACIONES
#============================
from __future__ import annotations

import streamlit as st

from src.base.constants import (
    STATE_LABELS,
    STATE_CODE_FROM_LABEL,
    GROUPINGS,
    GROUPING_TITLES,
    AVAILABLE_YEARS,
)
from src.runtime.charts_altair import build_participation_chart_altair
from app.ui_helpers import limit_categories
from src.runtime.maps_render import build_state_choropleth_plotly
from app.data_access import (
    get_tab_estado_artifact_cached,
    get_municipal_geometries_cached,
)

#============================
# ADECUACIÓN A NOMBRE DE OBJETO PARA CARGA DESDE data_access
#============================
def _get_tab_estado_filename(grouping_label: str) -> str:
    mapping = {
        "Mostrar por municipio": "tab_estado_municipio.parquet",
        "Mostrar por sexo": "tab_estado_sexo.parquet",
        "Mostrar por edad": "tab_estado_edad.parquet",
        "Mostrar por tipo de sección": "tab_estado_tipo_seccion.parquet",
    }

    if grouping_label not in mapping:
        raise ValueError(f"Grouping inválido: {grouping_label}")

    return mapping[grouping_label]

#============================
# DEF render_tab_estado(): Gestiona los elementos del TAB
#============================ 
def render_tab_estado() -> None:
    st.caption(
        "Selecciona un estado, año y categoría para analizar la participación electoral y el abstencionismo."
    )

    col_controls, col_results = st.columns([1, 3], gap="large")

    with col_controls:
        with st.container(border=True):
            st.subheader("Filtrar por")

            state_label = st.selectbox(
                "Entidad federativa 📍",
                options=sorted(STATE_LABELS.values()),
                help="Selecciona la entidad federativa.",
                key="tab_estado_state",
            )
            state_code = STATE_CODE_FROM_LABEL[state_label]

            year = st.selectbox(
                "Año 🗓️",
                options=list(AVAILABLE_YEARS),
                index=0,
                help="Selecciona el año.",
                key="tab_estado_year",
            )

            grouping_label = st.selectbox(
                "Categoría 🔭",
                options=list(GROUPINGS.keys()),
                help="Selecciona cómo quieres agrupar los datos.",
                key="tab_estado_grouping",
            )

            top_n: int | None = None
            if grouping_label == "Mostrar por municipio":
                top_n = st.number_input(
                    "Mostrar Top N municipios",
                    min_value=1,
                    max_value=600,
                    value=15,
                    step=1,
                    help=(
                        "Filtra un Top de municipios según la participación total. "
                        "El resto se agrupa como 'Otros'."
                    ),
                    key="tab_estado_topn",
                )

    with col_results:
        with st.status("Cargando datos...", expanded=False) as status:
            filename = _get_tab_estado_filename(grouping_label)
            df_view_all = get_tab_estado_artifact_cached(filename)
            status.write("Artefacto agregado cargado")

            view = df_view_all[
                (df_view_all["state_code"] == state_code)
                & (df_view_all["year"] == int(year))
            ].copy()
            status.write("Filtro por estado y año aplicado")

            if view.empty:
                status.update(label="Sin datos disponibles", state="error")
                st.warning("No hay datos disponibles para la combinación seleccionada.")
                return

            if grouping_label == "Mostrar por municipio":
                view = limit_categories(view, top_n=top_n, by="SV", others=True)

            status.update(label="Datos listos", state="complete")

        sv_total = int(view["SV"].sum())
        nv_total = int(view["NV"].sum())
        total_municipios = int(
            get_tab_estado_artifact_cached("tab_estado_municipio.parquet")
            .query("state_code == @state_code and year == @year")["categoria"]
            .nunique()
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Participación total en el estado", f"{sv_total:,}")
        m2.metric("Abstencionismo total en el estado", f"{nv_total:,}")
        m3.metric("Total de municipios", f"{total_municipios:,}")

        categoria_nombre = GROUPING_TITLES.get(grouping_label, grouping_label)
        title = (
            f"Composición de participación en {state_label} - {year}. "
            f"Según {categoria_nombre}"
        )

        with st.spinner("Renderizando visualización..."):
            chart = build_participation_chart_altair(view, title=title)
            st.altair_chart(chart, use_container_width=True)

    st.divider()

    st.subheader("Mapa municipal")

    col_map_controls, col_map_results = st.columns([1, 4], gap="large")

    with col_map_controls:
        with st.container(border=True):
            st.subheader("Ver mapa por")

            map_mode = st.selectbox(
                "Mostrar valores como:",
                options=["Porcentaje", "Total nominal"],
                index=0,
                help="Cambia entre porcentajes y valores absolutos.",
                key="tab_estado_map_mode",
            )

    with col_map_results:
        with st.status("Preparando mapa municipal...", expanded=False) as status:
            df_map_all = get_tab_estado_artifact_cached("tab_estado_mapa.parquet")
            status.write("Artefacto de mapa cargado")

            df_map = df_map_all[
                (df_map_all["state_code"] == state_code)
                & (df_map_all["year"] == int(year))
            ].copy()
            status.write("Filtro de mapa por estado y año aplicado")

            if df_map.empty:
                status.update(label="Sin datos disponibles", state="error")
                st.warning("No hay datos de mapa disponibles para la combinación seleccionada.")
                return

            gdf_municipios = get_municipal_geometries_cached()
            status.write("Geometrías municipales cargadas")

            gdf_map = gdf_municipios.merge(
                df_map,
                on="CVEGEO",
                how="inner",
                validate="1:1",
            )
            status.write("Unión entre geometrías y métricas completada")

            status.update(label="Mapa listo", state="complete")

        if map_mode == "Porcentaje":
            col_left, col_right = "sv_ratio", "nv_ratio"
        else:
            col_left, col_right = "SV", "NV"

        map_col1, map_col2 = st.columns(2, gap="large")

        with map_col1:
            fig_left = build_state_choropleth_plotly(
                gdf_map=gdf_map,
                column=col_left,
                state_name=state_label,
                year=int(year),
            )
            st.plotly_chart(fig_left, use_container_width=True)

        with map_col2:
            fig_right = build_state_choropleth_plotly(
                gdf_map=gdf_map,
                column=col_right,
                state_name=state_label,
                year=int(year),
            )
            st.plotly_chart(fig_right, use_container_width=True)