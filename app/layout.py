"""
layout.py
ARCHIVO ENCARGADO DE LA INTERFAZ GRÁFICA
"""

# ===========================
# IMPORTACIONES
# ===========================
import streamlit as st


# ===========================
# HEADER
# ===========================
def render_header() -> None:
    st.markdown(
        """
        <h1 style='text-align: center;'>
            Explorador de participación electoral 🗳️
        </h1>
        <p style='text-align: justify; text-align-last: center; font-size: 1rem; max-width: 900px; margin: 0 auto 0.75rem auto;'>
            Este sitio web es un proyecto para mi portafolio de trabajo como analista de datos.
            Aquí encontrarás visualizaciones para saber más acerca de la participación electoral
            en México, sus estados y municipios. Para ver más proyectos visita mi
            <a href="https://github.com/hucevaba1" target="_blank">Github</a>.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        .stTabs [data-baseweb="tab-list"] {
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ===========================
# FOOTER
# ===========================
def render_footer() -> None:
    st.divider()
    st.markdown(
        '<p class="footer" style="text-align: center;">'
        "Elaboración propia con base en datos de los Conteos Censales de Participación "
        "Ciudadana 2009-2024 del Instituto Nacional Electoral (INE)."
        "</p>",
        unsafe_allow_html=True,
    )