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
    plot_gdf = plot_gdf.to_crs(epsg=4326).reset_index(drop=True)

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

# =====================================================
# DEF build_state_choropleth_plotly(): CONSTRUYE EL MAPA COROPLÉTICO RUNTIME PARA ESTADOS
# =====================================================
def build_national_state_choropleth_plotly(
    gdf_map: gpd.GeoDataFrame,
    column: str = "sv_ratio",
    year: int | None = None,
    width: int = 1000,
    height: int = 500,
):
    """
    Construye un mapa coroplético nacional a nivel estado.
    """
    valid_columns = {"sv_ratio", "nv_ratio", "SV", "NV"}
    if column not in valid_columns:
        raise ValueError(f"column debe ser una de {valid_columns}")

    required_cols = ["state_code", "state_label", "geometry", "sv_ratio", "nv_ratio", "SV", "NV"]
    validate_required_columns(gdf_map, required_cols, context="maps")

    plot_gdf = gdf_map.copy()

    if plot_gdf.crs is None:
        raise ValueError("El GeoDataFrame no tiene CRS definido.")

    plot_gdf = plot_gdf[plot_gdf.geometry.notna()].copy()
    plot_gdf = plot_gdf.to_crs(epsg=4326).reset_index(drop=True)

    plot_gdf["feature_id"] = plot_gdf["state_code"].astype(str)

    if column == "sv_ratio":
        color_scale = [(0.0, "#ffffff"), (1.0, "#2e7d32")]
        title_text = "Participación estatal"
        colorbar_title = "%"
        range_color = (0, float(plot_gdf["sv_ratio"].max()))
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación: %{customdata[0]:.2%} | %{customdata[2]:,}<br>"
            "Abstención: %{customdata[1]:.2%} | %{customdata[3]:,}"
            "<extra></extra>"
        )
    elif column == "nv_ratio":
        color_scale = [(0.0, "#ffffff"), (1.0, "#b71c1c")]
        title_text = "Abstención estatal"
        colorbar_title = "%"
        range_color = (0, float(plot_gdf["nv_ratio"].max()))
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación: %{customdata[0]:.2%} | %{customdata[2]:,}<br>"
            "Abstención: %{customdata[1]:.2%} | %{customdata[3]:,}"
            "<extra></extra>"
        )
    elif column == "SV":
        color_scale = [(0.0, "#ffffff"), (1.0, "#2e7d32")]
        title_text = "Participación nominal estatal"
        colorbar_title = ""
        range_color = None
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación: %{customdata[0]:.2%} | %{customdata[2]:,}<br>"
            "Abstención: %{customdata[1]:.2%} | %{customdata[3]:,}"
            "<extra></extra>"
        )
    else:
        color_scale = [(0.0, "#ffffff"), (1.0, "#b71c1c")]
        title_text = "Abstención nominal estatal"
        colorbar_title = ""
        range_color = None
        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Participación: %{customdata[0]:.2%} | %{customdata[2]:,}<br>"
            "Abstención: %{customdata[1]:.2%} | %{customdata[3]:,}"
            "<extra></extra>"
        )

    geojson_dict = json.loads(plot_gdf[["feature_id", "geometry"]].to_json())

    for feature, fid in zip(geojson_dict["features"], plot_gdf["feature_id"]):
        feature["id"] = fid

    full_title = title_text
    if year is not None:
        full_title += f"<br><sup>México - {year}</sup>"

    fig = px.choropleth(
        plot_gdf,
        geojson=geojson_dict,
        locations="feature_id",
        featureidkey="id",
        color=column,
        color_continuous_scale=color_scale,
        range_color=range_color,
        hover_name="state_label",
        custom_data=["sv_ratio", "nv_ratio", "SV", "NV"],
    )

    fig.update_geos(
        fitbounds="geojson",
        visible=False,
    )

    fig.update_traces(
        marker_line_color="black",
        marker_line_width=0.7,
        hovertemplate=hovertemplate,
    )

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

# =====================================================
# DEF build_forecast_state_choropleth_plotly(): CONSTRUYE EL MAPA COROPLÉTICO RUNTIME PARA FORECAST
# =====================================================
def build_forecast_state_choropleth_plotly(
    gdf_map: gpd.GeoDataFrame,
    state_name: str,
    forecast_year: int = 2027,
    width: int = 1000,
    height: int = 480,
):
    """
    Construye un mapa coroplético estatal a nivel municipal para el pronóstico 2027.
    """
    required_cols = [
        "CVEGEO",
        "municipio",
        "geometry",
        "y_pred",
        "pi_lower",
        "pi_upper",
    ]
    validate_required_columns(gdf_map, required_cols, context="maps")

    plot_gdf = gdf_map.copy()

    if plot_gdf.crs is None:
        raise ValueError("El GeoDataFrame no tiene CRS definido.")

    plot_gdf = plot_gdf[plot_gdf.geometry.notna()].copy()
    plot_gdf = plot_gdf.to_crs(epsg=4326).reset_index(drop=True)

    plot_gdf["feature_id"] = plot_gdf["CVEGEO"].astype(str)
    plot_gdf["municipio_label"] = plot_gdf["municipio"].astype("string")

    geojson_dict = json.loads(plot_gdf[["feature_id", "geometry"]].to_json())

    for feature, fid in zip(geojson_dict["features"], plot_gdf["feature_id"]):
        feature["id"] = fid

    valid_preds = plot_gdf["y_pred"].dropna()
    max_val = float(valid_preds.max()) if not valid_preds.empty else 1.0

    fig = px.choropleth(
        plot_gdf,
        geojson=geojson_dict,
        locations="feature_id",
        featureidkey="id",
        color="y_pred",
        color_continuous_scale=[(0.0, "#ffffff"), (1.0, "#2e7d32")],
        range_color=(0, max_val),
        hover_name="municipio_label",
        custom_data=["y_pred", "pi_upper", "pi_lower"],
    )

    fig.update_geos(
        fitbounds="geojson",
        visible=False,
    )

    fig.update_traces(
        marker_line_color="black",
        marker_line_width=0.5,
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Valor predicho: %{customdata[0]:.2%}<br>"
            "Intervalo superior: %{customdata[1]:.2%}<br>"
            "Intervalo inferior: %{customdata[2]:.2%}"
            "<extra></extra>"
            ),
        )

    fig.update_layout(
        title=dict(
            text=f"Estimación municipal de participación - {state_name}<br><sup>{forecast_year}</sup>",
            x=0.02,
            xanchor="left",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(
            title="%",
            len=0.55,
            thickness=14,
            y=0.5,
            yanchor="middle",
        ),
        width=width,
        height=height,
    )

    return fig