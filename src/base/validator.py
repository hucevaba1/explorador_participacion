"""
validator.py
ARCHIVO PARA EXPORTAR FUNCIÓN DE VALIDACIÓN 
"""

# ---------------------------------------
# IMPORTACIONES
# ---------------------------------------
from __future__ import annotations

import pandas as pd

# ---------------------------------------
# DEF valided_required_columns(): 
# ---------------------------------------
def validate_required_columns(
    df: pd.DataFrame,
    required_cols: list[str],
    context: str | None = None,
) -> None:
    """
    Valida que un DataFrame contenga todas las columnas requeridas.

    Recibe:
        - df: DataFrame a validar.
        - required_cols: lista de columnas obligatorias.
        - context: nombre opcional del módulo, función o proceso
          para enriquecer el mensaje de error.

    Devuelve:
        - None

    Lanza:
        - ValueError si faltan columnas requeridas.
    """
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        if context:
            raise ValueError(
                f"Faltan columnas requeridas para {context}: {missing}"
            )
        raise ValueError(
            f"Faltan columnas requeridas: {missing}"
        )
    
