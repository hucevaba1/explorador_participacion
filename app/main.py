"""
main.py
Compositor principal de la aplicación Streamlit del proyecto
de participación electoral.

Este módulo:
- renderiza el encabezado,
- organiza la app en pestañas,
- delega cada flujo a su módulo correspondiente,
- y renderiza el pie de página.
"""

# -------------------------------------------------
# IMPORTACIÓN DE LIBRERÍAS
# -------------------------------------------------
from __future__ import annotations

import streamlit as st

from app.layout import render_header, render_footer
from app.tab_explorador import render_tab_explorador
from app.tab_modelo import render_tab_modelo


# -------------------------------------------------
# APP
# -------------------------------------------------
def main() -> None:
    render_header()

    tab_explorador, tab_modelo = st.tabs(
        ["Explorador", "Modelo predictivo"]
    )

    with tab_explorador:
        render_tab_explorador()

    with tab_modelo:
        render_tab_modelo()

    render_footer()


if __name__ == "__main__":
    main()