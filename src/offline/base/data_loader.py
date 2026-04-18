''' 
data_loader.py
# ARCHIVO DE CARGA DE DATOS PARA EL PROYECTO DE ANÁLISIS DE DATOS ELECTORALES:
# Este módulo se encarga de cargar los datos desde los archivos CSV ubicados en el directorio.
# Incluye funciones para:
# - Cargar datos de un año específico para todos los estados
# - Cargar datos de un estado específico para todos los años
# - Cargar todo el conjunto de datos.
'''

# --------------------------------
# IMPORTACIONES
# --------------------------------
from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

import pandas as pd
# =====================================================
# EXPRESIÓN REGULAR PARA NOMBRES DE ARCHIVOS
# ===================================================== 
FILENAME_RE = re.compile(
    r"^datosabiertos_deceyec_conteoscensales(?P<year>\d{4})_(?P<state>[a-z]{2,5})\.csv$")

# =====================================================
# Normalizador de alias luego de ver problemas con geometrías 
# ===================================================== 
STATE_CODE_ALIASES = {
    "tamps": "tam",
    "tam": "tam",
    "bcs": "bcs",
    "bc": "bc",
    "qroo": "qroo",
}
# =====================================================
# DEF _year_dir(): VALIDA QUE EL DIRECTORIO DE AÑO EXISTA
# =====================================================
def _year_dir(base_dir: str | Path, year: int) -> Path:
    base_path = Path(base_dir)
    year_path = base_path / "data" / str(year)

    if not year_path.exists():
        raise FileNotFoundError(f"No existe el directorio esperado: {year_path}")

    return year_path

# =====================================================
# DEF _read_election_csv(): LEE UN ARCHIVO CSV DE ELECCIÓN Y AGREGA COLUMNAS DE AÑO Y ESTADO DERIVADAS DEL NOMBRE DEL ARCHIVO
# =====================================================
def _read_electoral_csv(
    fp: Path,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    match = FILENAME_RE.match(fp.name)
    if not match:
        raise ValueError(f"Archivo con nombre inesperado: {fp.name}")

    year = int(match.group("year"))
    state_code = match.group("state").lower()
    state_code = STATE_CODE_ALIASES.get(state_code, state_code)

    df = pd.read_csv(fp, encoding=encoding, low_memory=False)
    df["year"] = year
    df["state_code"] = state_code
    return df

# =====================================================
# DEF load_data(): CARGA TODOS LOS DATOS DE LOS AÑOS ESPECIFICADOS, LOS CONCATENA Y AGREGA COLUMNAS DE AÑO Y ESTADO. 
# ===================================================== 
def load_data(
    base_dir: str | Path,
    years: Iterable[int] = (2009, 2012, 2015, 2018, 2021, 2024),
    encoding: str = "utf-8",
) -> pd.DataFrame:
    """
    Carga todos los CSV de los años especificados, los concatena y añade:
    - year
    - state_code
    """
    frames: list[pd.DataFrame] = []

    for year in years:
        year_dir = _year_dir(base_dir, int(year))

        for fp in sorted(year_dir.glob("*.csv")):
            frames.append(_read_electoral_csv(fp, encoding=encoding))

    if not frames:
        raise ValueError(
            "No se cargó ningún CSV. Revisa la ruta base y la estructura de carpetas."
        )

    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    df_all = load_data(base_dir=".")
    print(df_all.shape)
    print(df_all.columns)
    print(df_all.head())

# =====================================================
# DEF load_state_data(): CARGA LOS DATOS DE UN ESTADO ESPECÍFICO PARA LOS AÑOS ESPECIFICADOS, LOS CONCATENA Y AGREGA COLUMNAS DE AÑO Y ESTADO. 
# ===================================================== 
def load_state_data(
    base_dir: str | Path,
    state_code: str,
    years: Iterable[int] = (2009, 2012, 2015, 2018, 2021, 2024),
    encoding: str = "utf-8",
) -> pd.DataFrame:
    """
    Carga los CSV de un estado específico para los años indicados.
    Usa un código canónico de estado y resuelve alias al buscar archivos.
    """
    state_code = state_code.lower()
    state_code = STATE_CODE_ALIASES.get(state_code, state_code)

    frames: list[pd.DataFrame] = []

    for year in years:
        year_dir = _year_dir(base_dir, int(year))
        matched_fp: Path | None = None

        for fp in sorted(year_dir.glob("*.csv")):
            match = FILENAME_RE.match(fp.name)
            if not match:
                continue

            file_state_code = match.group("state").lower()
            file_state_code = STATE_CODE_ALIASES.get(file_state_code, file_state_code)

            if file_state_code == state_code:
                matched_fp = fp
                break

        if matched_fp is None:
            raise FileNotFoundError(
                f"No existe archivo para el estado canónico {state_code!r} en {year_dir}"
            )

        frames.append(_read_electoral_csv(matched_fp, encoding=encoding))

    return pd.concat(frames, ignore_index=True)

# =====================================================
# DEF load_year_data(): CARGA LOS DATOS DE UN AÑO ESPECÍFICO PARA LOS ESTADOS ESPECIFICADOS, LOS CONCATENA Y AGREGA COLUMNAS DE AÑO Y ESTADO.
# ===================================================== 
def load_year_data(
    base_dir: str | Path,
    year: int = 2024,
    encoding: str = "utf-8",
    states: Iterable[str] | None = None,
    strict_states: bool = True,
) -> pd.DataFrame:
    """
    Carga los CSV de un año específico para todos los estados o un subconjunto.
    """
    year_dir = _year_dir(base_dir, year)

    wanted: set[str] | None = None
    if states is not None:
        wanted = {
            STATE_CODE_ALIASES.get(state.lower(), state.lower())for state in states
            }

    frames: list[pd.DataFrame] = []
    loaded_states: set[str] = set()

    for fp in sorted(year_dir.glob("*.csv")):
        match = FILENAME_RE.match(fp.name)
        if not match:
            raise ValueError(f"Archivo con nombre inesperado: {fp.name}")

        year_from_name = int(match.group("year"))
        if year_from_name != year:
            raise ValueError(
                f"Archivo con año inesperado: {fp.name}. Se esperaba año {year}."
            )

        state_code = match.group("state").lower()
        state_code = STATE_CODE_ALIASES.get(state_code, state_code)

        if wanted is not None and state_code not in wanted:
            continue

        frames.append(_read_electoral_csv(fp, encoding=encoding))
        loaded_states.add(state_code)

    if wanted is not None and strict_states:
        missing = wanted - loaded_states
        if missing:
            raise FileNotFoundError(
                f"Faltan archivos para estos estados en {year_dir}: {sorted(missing)}"
            )

    if not frames:
        raise ValueError(f"No se cargó ningún CSV en {year_dir}")

    return pd.concat(frames, ignore_index=True)