"""
modelos.py
ARCHIVO DE MODELOS PARA LA PREDICCIÓN DE LA PROPORCIÓN DE ANALISIS ELECTORAL:
Incluye funciones para entrenar modelos de 
    - Regresión lineal
    - Ridge y 
    - Random forest.
También para realizar predicciones y extraer los coeficientes de modelos lineales.
"""

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------
from __future__ import annotations
import pandas as pd

from sklearn.linear_model import LinearRegression, Ridge

from src.base.validator import validate_required_columns
# --------------------------------------------------
# FEATURES (VARIABLES) UTILIZADAS EN LOS MODELOS
# --------------------------------------------------
DEFAULT_FEATURES: list[str] = [
    "lag_sv_ratio_1",
    "lag_sv_ratio_2", 
    "state_sv_ratio_mean_1",
]

# --------------------------------------------------
# DEF train_linear(): ENTRENAMIENTO DE MODELO DE REGRESIÓN LINEAL   
# --------------------------------------------------
def train_linear(
    train_df: pd.DataFrame,
    target: str,
    features: list[str] | None = None,
) -> LinearRegression:
    """
    Entrena un modelo de regresión lineal.
        Reecibe:
            - train_df: DataFrame de entrenamiento con las variables necesarias.
            - target: Nombre de la variable objetivo a predecir.
            - features: Lista de nombres de las variables predictoras a usar. Si es None, se usan las variables por defecto.
        Devuelve:
            - model: El modelo de regresión lineal entrenado.
    """
    features = features or DEFAULT_FEATURES
    validate_required_columns(train_df, features + [target], context="modelos",)

    X = train_df[features]
    y = train_df[target]

    model = LinearRegression()
    model.fit(X, y)
    return model

# --------------------------------------------------
# DEF train_ridge(): ENTRENAMIENTO DE MODELO DE REGRESIÓN RIDGE  
# --------------------------------------------------
def train_ridge(
    train_df: pd.DataFrame,
    target: str,
    alpha: float = 1.0,
    features: list[str] | None = None,
) -> Ridge:
    """
    Entrena un modelo de regresión Ridge.
        Reecibe:
            - train_df: DataFrame de entrenamiento con las variables necesarias.
            - target: Nombre de la variable objetivo a predecir.
            - alpha: Parámetro de regularización para Ridge. Por defecto es 1.0. # ESTOY USANDO UNO Y QUIZÁ POR ESO ESTÁ MODELANDO CASI COMO LINEAL.
            - features: Lista de nombres de las variables predictoras a usar. Si es None, se usan las variables por defecto.
        Devuelve:
            - model: El modelo de regresión Ridge entrenado.
    """
    features = features or DEFAULT_FEATURES
    validate_required_columns (train_df, features + [target], context="modelos")

    X = train_df[features]
    y = train_df[target]

    model = Ridge(alpha=alpha)
    model.fit(X, y)
    return model

# --------------------------------------------------
# DEF predict(): REALIZAR PREDICCIONES CON UN MODELO ENTRENADO
# --------------------------------------------------
def predict(
    model,
    df: pd.DataFrame,
    features: list[str] | None = None,
) -> pd.DataFrame:
    """
    Realiza predicciones con un modelo entrenado.
        Reecibe:
            - model: El modelo entrenado con el que se quieren hacer las predicciones.
            - df: DataFrame con las variables necesarias para hacer las predicciones.
            - features: Lista de nombres de las variables predictoras a usar. Si es None, se usan las variables por defecto.
        Devuelve:
            - out: DataFrame con las predicciones agregadas en una nueva columna "y_pred"
    """
    features = features or DEFAULT_FEATURES
    validate_required_columns(df, features, context="modelos")

    X = df[features]

    out = df.copy()
    out["y_pred"] = model.predict(X)
    return out

# --------------------------------------------------
# DEF extract_linear_coefficients(): EXTRAER LOS COEFICIENTES DE UN MODELO DE REGRESIÓN LINEAL
# --------------------------------------------------
def extract_linear_coefficients(
        model: LinearRegression | Ridge,
        features: list[str],
) -> pd.DataFrame:
    """
    Extrae los coeficientes de un modelo de regresión lineal.
        Reecibe:
            - model: El modelo de regresión lineal entrenado del que se quieren extraer los coeficientes.
            - features: Lista de nombres de las variables predictoras utilizadas en el modelo.
        Devuelve:
            - coef_df: DataFrame con los nombres de las variables y sus coeficientes, ordenados por la magnitud del coeficiente.
    """
    if not hasattr(model, "coef_"):
        raise ValueError (f"El modelo seleccionado no tiene coeficientes")
    
    coef_df = pd.DataFrame(
        {
            "feature": features,
            "coefficient": model.coef_
        }
    )

    coef_df = coef_df.sort_values(
        "coefficient",
        key=lambda s: s.abs(),
        ascending=False,
    ).reset_index(drop=True)

    return coef_df