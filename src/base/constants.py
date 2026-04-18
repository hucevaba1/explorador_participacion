''' 
constants.py
 ARCHIVO DE CONSTANTES PARA EL PROYECTO DE ANÁLISIS DE DATOS ELECTORALES
 Este módulo contiene todas las constantes utilizadas en el proyecto, incluyendo:
 - Claves y etiquetas de los estados
 - Años disponibles para análisis
 - Títulos de agrupación para visualizaciones
 - Dimensiones analíticas para segmentación de datos
 - Paleta de colores para series de tiempo
 - Etiquetas y claves para modelos predictivos
'''

# =====================================================
# CLAVES Y ETIQUETAS DE LOS ESTADOS
# =====================================================
STATE_LABELS: dict[str, str] = {
    "ags": "Aguascalientes",
    "bc": "Baja California",
    "bcs": "Baja California Sur",
    "camp": "Campeche",
    "coah": "Coahuila",
    "col": "Colima",
    "chis": "Chiapas",
    "chih": "Chihuahua",
    "cdmx": "Ciudad de México",
    "dgo": "Durango",
    "gto": "Guanajuato",
    "gro": "Guerrero",
    "hgo": "Hidalgo",
    "jal": "Jalisco",
    "mex": "Estado de México",
    "mich": "Michoacán",
    "mor": "Morelos",
    "nay": "Nayarit",
    "nl": "Nuevo León",
    "oax": "Oaxaca",
    "pue": "Puebla",
    "qro": "Querétaro",
    "qroo": "Quintana Roo",
    "slp": "San Luis Potosí",
    "sin": "Sinaloa",
    "son": "Sonora",
    "tab": "Tabasco",
    "tam": "Tamaulipas",
    "tlax": "Tlaxcala",
    "ver": "Veracruz",
    "yuc": "Yucatán",
    "zac": "Zacatecas",
}

STATE_CODE_FROM_LABEL: dict[str, str] = {v: k for k, v in STATE_LABELS.items()}

# =====================================================
# AÑOS DISPONIBLES 
# =====================================================
AVAILABLE_YEARS: tuple[int, ...] = (2024, 2021, 2018, 2015, 2012, 2009)

MODELING_YEARS: tuple[int, ...] = (2009, 2012, 2015, 2018, 2021, 2024)

# =====================================================
# TITULOS DE AGRUPACION
# =====================================================
GROUPING_TITLES: dict[str, str] = {
    "Mostrar por municipio": "Municipio",
    "Mostrar por sexo": "Sexo",
    "Mostrar por edad": "Edad",
    "Mostrar por tipo de sección": "Tipo de sección",
}

GROUPINGS: dict[str, str] = {
    "Mostrar por municipio": "MPIONOM",
    "Mostrar por sexo": "sexo",
    "Mostrar por edad": "generacion",
    "Mostrar por tipo de sección": "tipo_seccion",
}

# =====================================================
# DIMENSIONES ANALÍTICAS
# =====================================================
DIMENSIONS: dict[str, str] = {
    "sexo": "Sexo",
    "generacion": "Edad",
    "tipo_seccion": "Tipo de sección",
    "MPIONOM": "Municipio",
}

TIME_SERIES_DIMENSIONS = {
    "Sexo": "sexo",
    "Edad": "generacion",
    "Tipo de sección": "tipo_seccion",
}

# =====================================================
# PALETA DE COLORES PARA SERIES DE TIEMPO
# =====================================================
TIME_SERIES_PALETTE: list[str] = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
    "#AEC7E8", "#FFBB78", "#98DF8A", "#FF9896", "#C5B0D5",
    "#C49C94", "#F7B6D2", "#DBDB8D", "#9EDAE5", "#AD494A",
    "#8C6D31", "#E7BA52", "#A55194", "#C44E52", "#4C72B0",
    "#55A868", "#8172B2", "#CCB974", "#64B5CD", "#FFB27F",
    "#A585C7", "#F7CF89", "#D18C8C", "#7A9A7A", "#B79C7A", "#C2B0B0"
]

#---------------------------------------------------
# MODELO PREDICTIVO
#----------------------------------------------------
MODEL_LABELS = {
    "naive_last_value": "Estimador ingenuo",
    "linear_regression": "Regresión lineal",
    "ridge": "Ridge",
}

MODEL_KEYS_FROM_LABEL = {v: k for k, v in MODEL_LABELS.items()}

MODEL_TARGET_COL: str = "target_sv_ratio_next"

FEATURE_LABELS = {
    "lag_sv_ratio_1": "Proporción de participación anterior 1",
    "lag_sv_ratio_2": "Proporción de participación anterior 2",
    "state_sv_ratio_mean_1": "Proporción de participación media en el estado 1",
}
