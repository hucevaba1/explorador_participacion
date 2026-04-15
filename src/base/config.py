"""
config.py
Configuración de rutas del proyecto de análisis de datos electorales.

Este módulo centraliza las rutas principales del proyecto, incluyendo:
- la raíz del proyecto,
- el directorio de código fuente,
- el directorio de datos,
- el directorio de geometrías,
- y la ruta del shapefile municipal.
"""
# --------------------------------
# IMPORTACIONES
# --------------------------------  
from __future__ import annotations
from pathlib import Path

# =====================================================
# OBTENER RUTAS DE ARCHIVOS: RUTAS PRINCIPALES DEL PROYECTO
# =====================================================
PROJECT_ROOT = Path = Path(__file__).resolve().parents[2] # RAIZ DEL PROYECTO

SRC_DIR = Path = PROJECT_ROOT / "src" # DIRECTORIO DE CÓDIGOS FUENTE
DATA_DIR = Path = PROJECT_ROOT / "data" # DIRECTORIO DE DATOS
RAW_DATA_DIR = Path = DATA_DIR # DIRECTORIO DE DATOS CRUDOS
GEOMETRY_DIR = Path = DATA_DIR / "geometrias_municipios" # DIRECTORIO DE GEOMETRÍAS
SHAPEFILE_PATH = Path = GEOMETRY_DIR / "mun22cw.shp" # RUTA DEL ARCHIVO SHAPEFILE

APP_DIR = Path = SRC_DIR / "app" # DIRECTORIO DE APLICACIÓN
BASE_DIR = Path = SRC_DIR / "base" # DIRECTORIO DE MODULOS BASE
MAPS_DIR = Path = SRC_DIR / "maps" # DIRECTORIO DE MAPAS
VIEWS_DIR = Path = SRC_DIR / "views"  # DIRECTORIO DE VISTAS
MODELING_DIR = Path = SRC_DIR / "modeling"  # DIRECTORIO DE MODELADO

