"""
pipeline.py
ARCHIVO PRINCIPAL DEL FLUJO DE MODELADO Y EVALUACIÓN DE MODELOS DE REGRESIÓN PARA PRONÓSTICO DE SV RATIO DEL ANAÁLSIS ELECTORAL
"""
#=====================================
# IMPORTACIONES
#=====================================
from __future__ import annotations
from pathlib import Path
import pandas as pd

from src.base.pipeline import load_processed_multi_year
from src.base.constants import MODELING_YEARS, MODEL_TARGET_COL
from src.modeling.feature_engineering import build_modeling_dataframe
from src.modeling.baseline import baseline_naive_last_value
from src.modeling.validation import get_fixed_time_folds
from src.modeling.evaluation import evaluate_predictions
from src.modeling.diagnostics import build_prediction_frame
from src.modeling.modelos import (
    train_linear,
    train_ridge,
    predict,
    extract_linear_coefficients,
)

#=====================================
# CONSTANTES: FEATURES
#=====================================
MODEL_FEATURE_COLS: list[str] = [
    "lag_sv_ratio_1",
    "lag_sv_ratio_2",
    "state_sv_ratio_mean_1",
]

# ==========================================
# DEF _load_modeling_dataframe(): CARGA LOS DATOS PROCESADOS Y CONSTRUYE EL DATAFRAME DE MODELADO
# ==========================================
def _load_modeling_dataframe(base_dir: Path) -> pd.DataFrame:
    """
    Carga los datos procesados y construye el DataFrame base de modelado.
    """
    df_all = load_processed_multi_year(base_dir, MODELING_YEARS)
    return build_modeling_dataframe(df_all)

# =====================================================
# DEF _get_trainable_model_df(): DEVUELVE EL DATAFRAME DE MODELADO FILTRADO PARA SOLO INCLUIR FILAS CON FEATURES Y TARGET NO NULOS
# =====================================================
def _get_trainable_model_df(model_df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve solo las filas utilizables para entrenamiento/evaluación,
    es decir, aquellas con features y target completos.
    """
    return model_df.dropna(
        subset=MODEL_FEATURE_COLS + [MODEL_TARGET_COL]
    ).copy()

# =====================================================
# DEF _train_final_models(): ENTRENA LOS MODELOS FINALES (Lineal y Ridge)
# =====================================================
def _train_final_models(train_df: pd.DataFrame):
    """
    Entrena los dos modelos principales del pipeline.
    """
    linear_model = train_linear(
        train_df,
        MODEL_TARGET_COL,
        features=MODEL_FEATURE_COLS,
    )

    ridge_model = train_ridge(
        train_df,
        MODEL_TARGET_COL,
        alpha=1.0,  # Se deja explícito como decisión de configuración
        features=MODEL_FEATURE_COLS,
    )

    return linear_model, ridge_model

# =====================================================
# DEF run_model_diagnostics(): EJECUTA EL FLUJO COMPLETO DE MODELADO Y EVALUACIÓN DE MODELOS DE REGRESIÓN PARA PRONÓSTICO DE SV RATIO
# =====================================================
def run_model_diagnostics(
    base_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Ejecuta el flujo completo de modelado y evaluación fuera de muestra.

    Devuelve:
        - results_df: resultados por fold
        - summary_df: promedio por modelo
        - predictions_df: predicciones fuera de muestra
        - coef_linear: coeficientes del modelo lineal final
        - coef_ridge: coeficientes del modelo ridge final
    """
    model_df = _load_modeling_dataframe(base_dir)
    model_df = _get_trainable_model_df(model_df)

    folds = get_fixed_time_folds()

    results: list[dict] = []
    prediction_frames: list[pd.DataFrame] = []

    for fold in folds:
        train_years = fold["train_years"]
        test_year = fold["test_year"]

        train_df = model_df[model_df["year"].isin(train_years)].copy()
        test_df = model_df[model_df["year"] == test_year].copy()

        # --------------------------------------------------
        # ESTIMADOR INGENUO
        # --------------------------------------------------
        pred_df = baseline_naive_last_value(
            test_df,
            target_col=MODEL_TARGET_COL,
            lag_col="lag_sv_ratio_1",
        )

        metrics = evaluate_predictions(pred_df)
        metrics["model"] = "naive_last_value"
        metrics["test_year"] = test_year
        results.append(metrics)

        prediction_frames.append(
            build_prediction_frame(
                pred_df=pred_df,
                model_name="naive_last_value",
                target_col=MODEL_TARGET_COL,
                test_year=test_year,
            )
        )

        # --------------------------------------------------
        # REGRESIÓN LINEAL
        # --------------------------------------------------
        linear_model = train_linear(
            train_df,
            MODEL_TARGET_COL,
            features=MODEL_FEATURE_COLS,
        )

        pred_df = predict(
            linear_model,
            test_df,
            features=MODEL_FEATURE_COLS,
        )
        pred_df["y_true"] = pred_df[MODEL_TARGET_COL]

        metrics = evaluate_predictions(pred_df)
        metrics["model"] = "linear_regression"
        metrics["test_year"] = test_year
        results.append(metrics)

        prediction_frames.append(
            build_prediction_frame(
                pred_df=pred_df,
                model_name="linear_regression",
                target_col=MODEL_TARGET_COL,
                test_year=test_year,
            )
        )

        # --------------------------------------------------
        # RIDGE
        # --------------------------------------------------
        ridge_model = train_ridge(
            train_df,
            MODEL_TARGET_COL,
            alpha=1.0,  # Se deja explícito como decisión de configuración
            features=MODEL_FEATURE_COLS,
        )

        pred_df = predict(
            ridge_model,
            test_df,
            features=MODEL_FEATURE_COLS,
        )
        pred_df["y_true"] = pred_df[MODEL_TARGET_COL]

        metrics = evaluate_predictions(pred_df)
        metrics["model"] = "ridge"
        metrics["test_year"] = test_year
        results.append(metrics)

        prediction_frames.append(
            build_prediction_frame(
                pred_df=pred_df,
                model_name="ridge",
                target_col=MODEL_TARGET_COL,
                test_year=test_year,
            )
        )

    results_df = pd.DataFrame(results)

    summary_df = (
        results_df.groupby("model", as_index=False)[["mae", "rmse", "n"]]
        .mean()
        .sort_values("mae")
        .reset_index(drop=True)
    )

    predictions_df = pd.concat(prediction_frames, ignore_index=True)

    linear_model, ridge_model = _train_final_models(model_df)

    coef_linear = extract_linear_coefficients(
        linear_model,
        MODEL_FEATURE_COLS,
    )

    coef_ridge = extract_linear_coefficients(
        ridge_model,
        MODEL_FEATURE_COLS,
    )

    return results_df, summary_df, predictions_df, coef_linear, coef_ridge

# =====================================================
# DEF build_forecast_2027_outputs(): GENERA LOS PRONÓSTICOS PARA 2027 USANDO 2024 COMO ÚLTIMO AÑO OBSERVADO
# =====================================================
def build_forecast_2027_outputs(
    base_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Genera los pronósticos para 2027 usando 2024 como último año observado.
    """
    model_df = _load_modeling_dataframe(base_dir)

    train_df = _get_trainable_model_df(model_df)

    forecast_df = model_df[model_df["year"] == 2024].dropna(
        subset=MODEL_FEATURE_COLS
    ).copy()

    linear_model, ridge_model = _train_final_models(train_df)

    linear_pred = predict(
        linear_model,
        forecast_df,
        features=MODEL_FEATURE_COLS,
    ).copy()

    ridge_pred = predict(
        ridge_model,
        forecast_df,
        features=MODEL_FEATURE_COLS,
    ).copy()

    linear_out = linear_pred[
        ["CVEGEO", "municipio", "state_code", "LN", "y_pred"]
    ].copy()

    ridge_out = ridge_pred[
        ["CVEGEO", "municipio", "state_code", "LN", "y_pred"]
    ].copy()

    linear_out["model"] = "linear_regression"
    linear_out["forecast_year"] = 2027

    ridge_out["model"] = "ridge"
    ridge_out["forecast_year"] = 2027

    return linear_out, ridge_out
