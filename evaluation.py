"""
StockScope AI - Model Performance Evaluation Module
Calculates out-of-sample classification metrics on chronological test sets,
generates confusion matrices, and benchmarks against naive baselines.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from sklearn.pipeline import Pipeline


METRIC_EXPLANATIONS = {
    "Accuracy": "Proportion of total predictions that were correct (both Up and Down).",
    "Precision": "Out of all sessions predicted as UP, the percentage that actually moved UP. High precision minimizes false buy signals.",
    "Recall": "Out of all sessions that actually moved UP, the percentage correctly identified by the model.",
    "F1-Score": "Harmonic mean of Precision and Recall, balancing false positives and false negatives.",
    "ROC-AUC": "Area Under Receiver Operating Characteristic Curve. Evaluates discrimination ability across probability thresholds (0.5 = random chance, 1.0 = perfect).",
    "Majority Baseline": "Accuracy achieved by simply guessing the most frequent class every single day without any machine learning.",
    "Momentum Baseline": "Accuracy achieved by assuming tomorrow's direction will simply repeat today's price direction.",
}


def evaluate_model_performance(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    y_train: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """
    Evaluate a trained model pipeline on unseen chronological test data.
    """
    if X_test.empty or y_test.empty:
        raise ValueError("Cannot evaluate model on empty test dataset.")

    y_pred = pipeline.predict(X_test)
    y_true = y_test.values

    # Determine probability predictions if supported
    y_prob = None
    if hasattr(pipeline, "predict_proba"):
        try:
            y_prob = pipeline.predict_proba(X_test)[:, 1]
        except Exception:
            y_prob = None

    # Calculate basic classification metrics
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    # ROC-AUC requires both classes present in the test set
    unique_classes = np.unique(y_true)
    if len(unique_classes) > 1 and y_prob is not None:
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = None
    else:
        roc_auc = None

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Classification report dict
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    # Calculate Naive Baselines
    majority_acc = None
    if y_train is not None and not y_train.empty:
        majority_class = int(y_train.mode()[0])
        majority_pred = np.full_like(y_true, fill_value=majority_class)
        majority_acc = float(accuracy_score(y_true, majority_pred))

    # Momentum baseline (predict previous day's return direction)
    momentum_acc = None
    if "return_1d" in X_test.columns:
        mom_pred = (X_test["return_1d"] > 0).astype(int).values
        momentum_acc = float(accuracy_score(y_true, mom_pred))

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "matrix": cm.tolist(),
        },
        "classification_report": report,
        "test_sample_count": len(y_test),
        "class_balance_test": {
            "down_or_unchanged_0": int((y_true == 0).sum()),
            "up_1": int((y_true == 1).sum()),
        },
        "majority_baseline_acc": majority_acc,
        "momentum_baseline_acc": momentum_acc,
        "beats_majority_baseline": (acc > majority_acc) if majority_acc is not None else None,
        "beats_momentum_baseline": (acc > momentum_acc) if momentum_acc is not None else None,
    }


def compare_all_models(
    models_dict: Dict[str, Pipeline],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    y_train: Optional[pd.Series] = None
) -> pd.DataFrame:
    """
    Generate a summary comparison DataFrame for all models evaluated on test data.
    """
    rows = []
    for name, pipe in models_dict.items():
        res = evaluate_model_performance(pipe, X_test, y_test, y_train)
        rows.append({
            "Model": name,
            "Accuracy": f"{res['accuracy'] * 100:.2f}%",
            "Precision": f"{res['precision'] * 100:.2f}%",
            "Recall": f"{res['recall'] * 100:.2f}%",
            "F1-Score": f"{res['f1_score'] * 100:.2f}%",
            "ROC-AUC": f"{res['roc_auc']:.3f}" if res["roc_auc"] is not None else "N/A",
            "Beats Majority": "Yes ✅" if res["beats_majority_baseline"] else "No ❌",
            "Beats Momentum": "Yes ✅" if res["beats_momentum_baseline"] else "No ❌",
        })

    # Add baseline rows for clear academic comparison
    if y_train is not None and not y_train.empty:
        majority_class = int(y_train.mode()[0])
        maj_pred = np.full(len(y_test), fill_value=majority_class)
        maj_acc = accuracy_score(y_test, maj_pred)
        rows.append({
            "Model": "Baseline: Majority Class",
            "Accuracy": f"{maj_acc * 100:.2f}%",
            "Precision": "-",
            "Recall": "-",
            "F1-Score": "-",
            "ROC-AUC": "-",
            "Beats Majority": "-",
            "Beats Momentum": "-",
        })

    if "return_1d" in X_test.columns:
        mom_pred = (X_test["return_1d"] > 0).astype(int).values
        mom_acc = accuracy_score(y_test, mom_pred)
        rows.append({
            "Model": "Baseline: Prev-Day Momentum",
            "Accuracy": f"{mom_acc * 100:.2f}%",
            "Precision": "-",
            "Recall": "-",
            "F1-Score": "-",
            "ROC-AUC": "-",
            "Beats Majority": "-",
            "Beats Momentum": "-",
        })

    return pd.DataFrame(rows)
