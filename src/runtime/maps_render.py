"""
maps_render.py
Funciones de renderizado de mapas para la capa runtime de la app.
"""

# ==========================
# IMPORTACIONES
# ==========================
from __future__ import annotations

import json

import geopandas as gpd
import plotly.express as px

from src.base.validator import validate_required_columns


# =====================================================
# DEF build_state_choropleth_plotly(): CONSTRUYE EL MAPA COROPLÉTICO RUNTIME
# =====================================================
def build_state_choropleth_plotly(
    gdf_map: gpd.GeoDataFrame,
    column: str = "sv_ratio",
    state_name: str | None = None,
    year: int | None = None,
    width: int = 1000,
    height: int = 500,
):
    """
    Construye un mapa coroplético de un estado específico usando Plotly Express.
    """
    valid_columns = {"sv_ratio", "nv_ratio", "SV", "NV"}
    if column not in valid_columns:
        raise ValueError(f"column debe ser una de {valid_columns}")

    required_cols = ["CVEGEO", "geometry", "sv_ratio", "nv_ratio", "SV", "NV"]
    validate_required_columns(gdf_map, required_cols, context="maps")

    plot_gdf = gdf_map.copy()

    if plot_gdf.crs is None:
        raise ValueError("El GeoDataFrame no tiene CRS definido.")

    if "MPIONOM" in plot_gdf.columns:
        municipio_base = plot_gdf["MPIONOM"]
    elif "NOMGEO" in plot_gdf.columns:
        municipio_base = plot_gdf["NOMGEO"]
    else:
        raise ValueError(
            "Se requiere MPIONOM o NOMGEO para construir el hover del mapa."
        )

    plot_gdf["municipio_label"] = municipio_base.astype("string")
    plot_gdf["CVEGEO"] = plot_gdf["CVEGEO"].astype(str)

    plot_gdf = plot_gdf[plot_gdf.geometry.notna()].copy()
    plot_gdf = plot_gdf.to_crs(epsg=4326)

    plot_gdf = plot_gdf.explode(index_parts=False).reset_index(drop=True)
    plot_gdf["feature_id"] = plot_gdf["CVEGEO"]

    custom_data_cols = ["sv_ratio", "nv_ratio", "SV", "NV"]

    if column == "sv_ratio":
        color_scale = "Greens"
        title_text = "Participación municipal"
        colorbar_title = "%"
        range_color = (0, 1)
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación: %{customdata[0]:.2%}<br>"
            "Abstencionismo: %{customdata[1]:.2%}"
            "<extra></extra>"
        )
    elif column == "nv_ratio":
        color_scale = "Reds"
        title_text = "Abstencionismo municipal"
        colorbar_title = "%"
        range_color = (0, 1)
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación: %{customdata[0]:.2%}<br>"
            "Abstencionismo: %{customdata[1]:.2%}"
            "<extra></extra>"
        )
    elif column == "SV":
        color_scale = "Greens"
        title_text = "Participación total municipal"
        colorbar_title = ""
        range_color = None
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación total: %{customdata[2]:,}<br>"
            "Abstencionismo total: %{customdata[3]:,}"
            "<extra></extra>"
        )
    else:
        color_scale = "Reds"
        title_text = "Abstencionismo total municipal"
        colorbar_title = ""
        range_color = None
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación total: %{customdata[2]:,}<br>"
            "Abstencionismo total: %{customdata[3]:,}"
            "<extra></extra>"
        )

    geojson_dict = json.loads(
        plot_gdf[["feature_id", "geometry"]].to_json()
    )

    for feature, fid in zip(geojson_dict["features"], plot_gdf["feature_id"]):
        feature["id"] = fid

    subtitle_parts = []
    if state_name:
        subtitle_parts.append(state_name)
    if year is not None:
        subtitle_parts.append(str(year))
    subtitle_text = " - ".join(subtitle_parts)

    fig = px.choropleth(
        plot_gdf,
        geojson=geojson_dict,
        locations="feature_id",
        featureidkey="id",
        color=column,
        color_continuous_scale=color_scale,
        range_color=range_color,
        hover_name="municipio_label",
        custom_data=custom_data_cols,
    )

    fig.update_geos(
        fitbounds="geojson",
        visible=False,
    )

    fig.update_traces(
        marker_line_color="black",
        marker_line_width=0.6,
        hovertemplate=hovertemplate,
    )

    full_title = title_text
    if subtitle_text:
        full_title += f"<br><sup>{subtitle_text}</sup>"

    fig.update_layout(
        title=dict(text=full_title, x=0.02, xanchor="left"),
        margin=dict(l=0, r=0, t=30, b=0),
        coloraxis_colorbar=dict(
            title=colorbar_title,
            len=0.55,
            thickness=14,
            y=0.5,
            yanchor="middle",
        ),
        width=width,
        height=height,
    )

    return fig