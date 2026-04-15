"""
app.py
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
from app.tab_estado import render_tab_estado
from app.tab_anios import render_tab_anios
from app.tab_modelo import render_tab_modelo

# -------------------------------------------------
# APP
# -------------------------------------------------
def main() -> None:
    render_header()

    tab_estado, tab_anios, tab_modelo = st.tabs(
        ["Por estados", "Por años", "Modelo predictivo"]
    )

    with tab_estado:
        render_tab_estado()

    with tab_anios:
        render_tab_anios()

    with tab_modelo:
        render_tab_modelo()

    render_footer()

if __name__ == "__main__":
    main()