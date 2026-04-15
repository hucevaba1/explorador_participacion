'''
charts_matplotlib.py
ARCHIVO ENCARGADO DE LOS GRÁFICOS CON MATPLOTLIB
TODOS ESTÁN COMENTADOS PORQUE SE DECIDIÓ USAR ALTÁIR PARA LOS GRÁFICOS PRINCIPALES, 
PERO SE MANTIENEN PARA DEJAR REGISTRO Y POR SI SE REQUIEREN
'''

#============================
# IMPORTACIONES
#============================
from __future__ import annotations
import matplotlib.pyplot as plt
import pandas as pd

# =====================================================
# DEF build_participation_figure_matplotlib(): DEVUELVE UNA FIGURA Y EJES DE MATPLOTLIB A PARTIR DEL VIEW PARA LA PESTAÑA POR ESTADO
# =====================================================
def build_participation_figure_matplotlib(
    view: pd.DataFrame,
    include_abstentions: bool = False,
    categoria_nombre: str = "categoría",
    title: str | None = None,
    figsize: tuple[int, int] = (14, 7),
) -> tuple[plt.Figure, plt.Axes]:
    """
    Devuelve una figura y ejes de Matplotlib a partir del view.
    Recibe:
        - view: DataFrame con el view model para la pestaña Por estado, con las columnas necesarias para construir la figura
        - include_abstentions: si incluir o no el abstencionismo en la figura (por defecto False, solo muestra participación)
        - categoria_nombre: nombre de la categoría para el título de la figura (por defecto "categoría")
        - title: título de la figura (por defecto None, se construye automáticamente a partir de categoria_nombre)
        - figsize: tamaño de la figura (por defecto (14, 7))
    Devuelve:
        - fig: figura de Matplotlib construida a partir del view
    """
    if title is None:
        title = f"% Participación electoral por {categoria_nombre}"

    df_plot = view.copy().sort_values("SV", ascending=False)
    categorias = df_plot["categoria"].astype(str).tolist()
    sv_pct = (df_plot["sv_ratio"] * 100).to_numpy()
    sv_nom = df_plot["SV"].to_numpy()

    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    ax.set_facecolor("white")

    if not include_abstentions:
        ax.barh(categorias, sv_pct, color="#8fbc8f", edgecolor="none", linewidth=0)

        for i, (pct, nom) in enumerate(zip(sv_pct, sv_nom)):
            ax.text(
                pct + 0.5,
                i,
                f"{pct:.1f}% ({nom:,})",
                va="center",
                ha="left",
                fontsize=10,
            )

        ax.set_xlabel("% Participación sobre lista nominal")

    else:
        nv_pct = (df_plot["nv_ratio"] * 100).to_numpy()
        nv_nom = df_plot["NV"].to_numpy()

        ax.barh(
            categorias,
            sv_pct,
            color="#8fbc8f",
            edgecolor="none",
            linewidth=0,
            label="Participación",
        )
        ax.barh(
            categorias,
            nv_pct,
            left=sv_pct,
            color="#CD5C5C",
            edgecolor="none",
            linewidth=0,
            label="Abstencionismo",
        )

        for i, (svp, nvp, svn, nvn) in enumerate(zip(sv_pct, nv_pct, sv_nom, nv_nom)):
            if svp >= 8:
                ax.text(
                    svp / 2,
                    i,
                    f"{svp:.1f}%\n({svn:,})",
                    va="center",
                    ha="center",
                    fontsize=9,
                )
            else:
                ax.text(
                    svp + 0.5,
                    i,
                    f"{svp:.1f}% ({svn:,})",
                    va="center",
                    ha="left",
                    fontsize=9,
                )

            if nvp >= 8:
                ax.text(
                    svp + nvp / 2,
                    i,
                    f"{nvp:.1f}%\n({nvn:,})",
                    va="center",
                    ha="center",
                    fontsize=9,
                )
            else:
                ax.text(
                    svp + nvp + 0.5,
                    i,
                    f"{nvp:.1f}% ({nvn:,})",
                    va="center",
                    ha="left",
                    fontsize=9,
                )

        ax.set_xlabel("% sobre lista nominal")
        max_total = (sv_pct + nv_pct).max()
        ax.set_xlim(0, max(100, max_total + 5))
        ax.legend(loc="lower right", frameon=False)

    for spine in ["right", "top", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(axis="y", labelsize=9)
    ax.set_title(title, pad=12, fontweight="bold")
    fig.tight_layout()

    return fig, ax

# =====================================================
# DEF build_participation_figure(): WRAPPER PARA NO ROMPER IMPORTS EXISTENTES
# ===================================================== 
def build_participation_figure(*args, **kwargs):
    """
    Wrapper para no romper imports existentes.
    """
    return build_participation_figure_matplotlib(*args, **kwargs)