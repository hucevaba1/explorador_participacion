"""
tab_modelo.py
ARCHIVO ENCARGADO DE LA PESTAÑA DE ANÁLISIS POR MODELO PREDICTIVO
"""
#============================
# IMPORTACIONES
#============================
from __future__ import annotations

import streamlit as st

from src.base.constants import (
    MODEL_LABELS,
    FEATURE_LABELS,
)
from src.runtime.forecast_views import plot_forecast_ranked
from src.runtime.model_diagnostics import (
    plot_predicted_vs_real,
    plot_error_distribution,
    build_error_map_frame,
    build_error_choropleth_plotly,
)
from app.data_access import (
    get_model_artifact_cached,
    get_municipal_geometries_cached,
)

#--------------------------------------------------
# DEF _render_diagnostic_panel(): Genera el panel para cualquier modelo dado.
#--------------------------------------------------
def _render_diagnostics_panel(
    predictions_df,
    gdf_municipios,
    model_name: str,
    model_title: str,
    selected_year: int,
    scatter_caption: str,
    hist_caption: str,
    error_map_caption: str,
    abs_error_map_caption: str,
) -> None:
    fig_pred_real, _ = plot_predicted_vs_real(
        predictions_df,
        model_name=model_name,
        test_year=selected_year,
    )

    fig_error_dist, _ = plot_error_distribution(
        predictions_df,
        model_name=model_name,
        test_year=selected_year,
    )

    gdf_error = build_error_map_frame(
        predictions_df=predictions_df,
        gdf_municipios=gdf_municipios,
        model_name=model_name,
        test_year=selected_year,
    )

    fig_map_error = build_error_choropleth_plotly(
        gdf_error,
        color_col="error",
        title=f"Error municipal - {model_title} - {selected_year}",
    )

    fig_map_abs_error = build_error_choropleth_plotly(
        gdf_error,
        color_col="abs_error",
        title=f"Error absoluto municipal - {model_title} - {selected_year}",
    )

    row1_col1, row1_col2 = st.columns(2, gap="large")
    row2_col1, row2_col2 = st.columns(2, gap="large")

    with row1_col1:
        st.pyplot(fig_pred_real, clear_figure=True)
        st.caption(scatter_caption)

    with row1_col2:
        st.pyplot(fig_error_dist, clear_figure=True)
        st.caption(hist_caption)

    with row2_col1:
        st.plotly_chart(fig_map_error, use_container_width=True)
        st.caption(error_map_caption)

    with row2_col2:
        st.plotly_chart(fig_map_abs_error, use_container_width=True)
        st.caption(abs_error_map_caption)

# -------------------------------------------------
# DEF render_tab_modelo(): Gestiona los elementos del TAB
# -------------------------------------------------
def render_tab_modelo() -> None:
    st.caption(
        "Comparación de modelos predictivos para anticipar la proporción de participación municipal en la siguiente elección."
    )

    with st.status("Cargando artefactos del modelo...", expanded=False) as status:
        summary_df = get_model_artifact_cached("model_summary.parquet")
        status.write("Resumen de modelos cargado")

        predictions_df = get_model_artifact_cached("model_predictions.parquet")
        status.write("Predicciones fuera de muestra cargadas")

        coef_linear = get_model_artifact_cached("model_coef_linear.parquet")
        coef_ridge = get_model_artifact_cached("model_coef_ridge.parquet")
        status.write("Coeficientes cargados")

        linear_2027_df = get_model_artifact_cached("forecast_linear_2027.parquet")
        ridge_2027_df = get_model_artifact_cached("forecast_ridge_2027.parquet")
        status.write("Pronósticos 2027 cargados")

        gdf_municipios = get_municipal_geometries_cached()
        status.write("Geometrías municipales cargadas")

        status.update(label="Artefactos listos", state="complete")

    if summary_df.empty:
        st.error("No fue posible generar el resumen de modelos.")
        return

    st.markdown(
        """
        En esta sección encontrarás la comparación entre un estimador ingenuo y dos modelos predictivos para estimar la proporción de participación municipal en la siguiente elección:
        un estimador ingenuo, una regresión lineal y un modelo Ridge. Los modelos se entrenan con información histórica del
        propio municipio y del contexto estatal, usando como regresores la proporción de participación en elecciones anteriores
        y la proporción media de participación del estado.

        El principal hallazgo es que ambos modelos lineales superan al estimador ingenuo y que el error de predicción disminuye
        conforme aumenta el tamaño del electorado municipal. Esto significa que **la participación es más predecible en municipios
        grandes y más volátil en municipios pequeños**, lo cual es consistente con la literatura académica sobre el tema.

        Aquí están algunas definiciones que te ayudarán a entender más fácilmente esta sección:

        * **MAE** es el error absoluto promedio, mientras más pequeño, mejor.
        * **RMSE** penaliza más los errores grandes, por lo que ayuda a identificar modelos que fallan con mayor fuerza en algunos municipios.
        * **Regresores** son las variables que utiliza el modelo para hacer la predicción.
        * **Coeficientes** indican cuánto pesa cada uno de los regresores dentro del modelo.
        """
    )

    st.divider()

    st.subheader("Comparación de modelos")

    c1, c2, c3 = st.columns(3)
    best_row = summary_df.iloc[0]

    c1.metric(
        "Mejor modelo",
        MODEL_LABELS.get(best_row["model"], str(best_row["model"])),
    )
    c2.metric("MAE promedio mínimo", f"{best_row['mae']:.3f}")
    c3.metric("RMSE promedio mínimo", f"{best_row['rmse']:.3f}")

    summary_df_display = summary_df.copy()
    summary_df_display["model"] = summary_df_display["model"].map(MODEL_LABELS)

    st.dataframe(summary_df_display, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Coeficientes de los modelos")

    coef_linear_display = coef_linear.copy()
    coef_linear_display["feature"] = coef_linear_display["feature"].map(
        FEATURE_LABELS
    )
    coef_linear_display = coef_linear_display.rename(
        columns={
            "feature": "Regresores",
            "coefficient": "Coeficientes",
        }
    )

    coef_ridge_display = coef_ridge.copy()
    coef_ridge_display["feature"] = coef_ridge_display["feature"].map(
        FEATURE_LABELS
    )
    coef_ridge_display = coef_ridge_display.rename(
        columns={
            "feature": "Regresores",
            "coefficient": "Coeficientes",
        }
    )

    col_coef1, col_coef2 = st.columns(2, gap="large")

    with col_coef1:
        st.markdown("**Regresión lineal**")
        st.latex(r"\hat{y}_{t+1} = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \beta_3 x_3")
        st.dataframe(coef_linear_display, use_container_width=True, hide_index=True)

        fig_linear_2027, _ = plot_forecast_ranked(
            linear_2027_df,
            model_display_name="Regresión lineal",
        )
        st.pyplot(fig_linear_2027, clear_figure=True)

        st.caption(
            "La línea muestra la estimación puntual de participación municipal esperada para 2027. "
            "La banda sombreada representa un intervalo de predicción aproximado construido a partir del error fuera de muestra del modelo."
        )

    with col_coef2:
        st.markdown("**Ridge**")
        st.latex(
            r"\hat{y}_{t+1} = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \beta_3 x_3,\quad \mathrm{con\ penalización}\ \lambda \sum_{j=1}^{p}\beta_j^2"
        )
        st.dataframe(coef_ridge_display, use_container_width=True, hide_index=True)

        fig_ridge_2027, _ = plot_forecast_ranked(
            ridge_2027_df,
            model_display_name="Ridge",
        )
        st.pyplot(fig_ridge_2027, clear_figure=True)

        st.caption(
            "La línea muestra la estimación puntual de participación municipal esperada para 2027. "
            "La banda sombreada representa un intervalo de predicción aproximado construido a partir del error fuera de muestra del modelo."
        )

    st.divider()

    st.subheader("Diagnósticos visuales")
    st.caption(
        "Los siguientes gráficos muestran la relación entre los valores reales y predichos, la distribución de los errores y el mapa de errores en la estimación para 2021. Su objetivo es facilitar la comparación del desempeño entre los modelos."
    )

    diag_tab_linear, diag_tab_ridge = st.tabs(["Regresión lineal", "Ridge"])

    with diag_tab_linear:
        _render_diagnostics_panel(
            predictions_df=predictions_df,
            gdf_municipios=gdf_municipios,
            model_name="linear_regression",
            model_title="Regresión lineal",
            selected_year=2021,
            scatter_caption=(
                "Este gráfico compara el valor real observado con el valor predicho por el modelo. "
                "Mientras más cerca estén los puntos de la diagonal, mejor es el ajuste. "
                "Los valores para los municipios más pequeños son los que más se alejan de la diagonal."
            ),
            hist_caption=(
                "Este histograma muestra cómo se distribuyen los errores de predicción. "
                "Un modelo bien calibrado tiende a concentrar sus errores cerca de cero y tener una distribución simétrica."
            ),
            error_map_caption=(
                "Este mapa representa el error con signo. Valores positivos indican sobreestimación del modelo "
                "y valores negativos, subestimación de la participación."
            ),
            abs_error_map_caption=(
                "Este mapa muestra la magnitud del error sin importar su signo. "
                "Sirve para identificar los municipios donde el modelo falla más."
            ),
        )

    with diag_tab_ridge:
        _render_diagnostics_panel(
            predictions_df=predictions_df,
            gdf_municipios=gdf_municipios,
            model_name="ridge",
            model_title="Ridge",
            selected_year=2021,
            scatter_caption=(
                "Este gráfico compara el valor real observado con el valor predicho por el modelo. "
                "Mientras más cerca estén los puntos de la diagonal, mejor es el ajuste."
            ),
            hist_caption=(
                "Este histograma muestra cómo se distribuyen los errores de predicción. "
                "Un modelo bien calibrado tiende a concentrar sus errores cerca de cero."
            ),
            error_map_caption=(
                "Este mapa representa el error con signo. Valores positivos indican sobreestimación del modelo "
                "y valores negativos, subestimación."
            ),
            abs_error_map_caption=(
                "Este mapa muestra la magnitud del error sin importar su signo. "
                "Sirve para identificar los municipios donde el modelo falla más."
            ),
        )

    st.divider()